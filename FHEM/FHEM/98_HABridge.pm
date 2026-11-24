package main;

use strict;
use warnings;
use bytes ();
use feature qw(bitwise);
use Digest::SHA qw(sha256_hex);
use Encode qw(decode encode FB_CROAK);
use File::Temp ();
use Fcntl qw(O_WRONLY O_CREAT O_EXCL);
use Errno qw(EAGAIN EWOULDBLOCK EINTR);
use IO::Socket::INET;
use IO::Socket::SSL qw(SSL_WANT_READ SSL_WANT_WRITE SSL_VERIFY_NONE $SSL_ERROR);
use IO::Socket::SSL::Utils qw(CERT_create CERT_free KEY_free PEM_cert2string PEM_key2string);
use MIME::Base64 qw(decode_base64 encode_base64);
use JSON::PP ();
use Scalar::Util qw(isweak refaddr weaken);
use Socket qw(AF_INET IPPROTO_TCP TCP_NODELAY inet_pton);
use Time::HiRes qw(gettimeofday clock_gettime CLOCK_MONOTONIC);

our ($readingFnAttributes, @structChangeHist, %defs, %attr, %modules, %selectlist, %logInform, $init_done, $unicodeEncoding);

use constant {
    HAB_MODULE_VERSION => '0.9.44',
    HAB_FRAME_LIMIT => 65536,
    HAB_QUEUE_LIMIT => 262144,
    HAB_IO_BUDGET   => 8192,
    HAB_READ_LIMIT  => 128,
    HAB_GROUP_LIMIT => 128,
    HAB_REQUEST_YIELD => 0.010,
    HAB_SLOW_REQUEST => 0.050,
    HAB_STARTUP_SET_LIMIT => 128,
};

my $hab_json = JSON::PP->new->utf8->max_depth(12)->max_size(HAB_FRAME_LIMIT);
my $hab_has_devel_size;

{
    package HABridge::Socket;
    use parent -norequire, 'IO::Socket::SSL';

    sub close {
        my ($socket, @options) = @_;
        my %options = ref($options[0]) eq 'HASH' ? %{$options[0]} : @options;
        # TcpServer_Close uses Perl's built-in close on the child's tied TLS
        # handle. Closing a duplicate must never send TLS close_notify.
        $options{SSL_no_shutdown} = 1;
        return $socket->SUPER::close(\%options);
    }
}

sub HABridge_Initialize {
    my ($module) = @_;
    $module->{DefFn} = 'HABridge_Define';
    $module->{UndefFn} = 'HABridge_Undef';
    $module->{NotifyFn} = 'HABridge_Notify';
    $module->{AttrFn} = 'HABridge_Attr';
    $module->{GetFn} = 'HABridge_Get';
    $module->{AttrList} = join(' ', 'allowConfigSave:0,1 disable:0,1 memoryDiagnostics bridgeDiagnostics:0,1', $readingFnAttributes // '');
    for my $bridge (values %defs) {
        next unless ($bridge->{TYPE} // '') eq 'HABridge';
        $bridge->{MODULE_VERSION} = HAB_MODULE_VERSION;
        HABridge_RemoveLegacyMemoryReadings($bridge);
        my $state = $bridge->{helper}{hab} or next;
        delete $state->{memory_baseline};
        $state->{diagnostics} = AttrVal($bridge->{NAME}, 'bridgeDiagnostics', 0);
        HABridge_RegisterListener($bridge, $state, $state->{listener}) if $state->{listener};
        if (my $client = $state->{client}) {
            # FHEM reload keeps the existing sockets and their callback references.
            weaken($client->{bridge}) if $client->{bridge} && !isweak($client->{bridge});
            $state->{connections} //= 1;
            if ($client->{socket}->isa('IO::Socket::SSL')) {
                bless $client->{socket}, 'HABridge::Socket';
            }
            $bridge->{CD} = $client->{socket};
            $client->{directReadFn} = \&HABridge_OnReadable;
            my $writer = $selectlist{"$client->{key}:write"};
            $writer->{directReadFn} = \&HABridge_IgnoreReadable if $writer;
            $writer->{directWriteFn} = \&HABridge_OnWritable if $writer;
        }
        my $status = $bridge->{READINGS}{state}{VAL} // '';
        $state->{status} //= $status if $status =~ /\A(?:online|offline|error|disabled)\z/;
        HABridge_DiagnosticTimer($bridge, AttrVal($bridge->{NAME}, 'memoryDiagnostics', 0));
    }
}

sub HABridge_Define {
    my ($bridge, $definition) = @_;
    $bridge->{MODULE_VERSION} = HAB_MODULE_VERSION;
    my (undef, undef, $ha_ip, $port, $token, @extra) = split ' ', $definition;
    return 'Usage: define <name> HABridge <HA-IPv4> <port> <secret>'
        unless defined($ha_ip) && inet_pton(AF_INET, $ha_ip) &&
        defined($port) && $port =~ /\A[0-9]{1,5}\z/ && $port >= 1024 && $port <= 65535 &&
        defined($token) && $token =~ /\A[A-Za-z0-9_-]{32,128}\z/ && !@extra;

    my $old = $bridge->{helper}{hab};
    if ($old && $old->{port} == $port) {
        HABridge_Close($old->{client}) if $old->{client};
        @$old{qw(ha_ip token)} = ($ha_ip, $token);
        return undef;
    }

    # Disk access and key generation happen at definition time, outside socket callbacks.
    my ($tls, $fingerprint) = eval { HABridge_TlsIdentity($port) };
    return 'HABridge: could not prepare the local TLS certificate' unless $tls;
    my $instance_id = getUniqueId();
    return 'HABridge: no stable FHEM instance ID available' unless HABridge_Token($instance_id);
    my $server_id = sha256_hex("HABridge:$instance_id");

    my $disabled = AttrVal($bridge->{NAME}, 'disable', 0) eq '1';
    my $listener = $disabled ? undef : HABridge_Listen($port);
    return "HABridge: cannot bind TLS port $port: $!" unless $disabled || $listener;

    HABridge_Undef($bridge) if $old;
    my $key = "HABridge:" . refaddr($bridge) . ":listener";
    my $state = $bridge->{helper}{hab} = {
        tls => $tls, ha_ip => $ha_ip, token => $token, server_id => $server_id,
        revision => 1, stream_number => 0, disabled => $disabled,
        epoch => sprintf('%d:%.6f', $$, scalar gettimeofday()),
        diagnostics => AttrVal($bridge->{NAME}, 'bridgeDiagnostics', 0),
        listener_key => $key, port => $port,
    };
    HABridge_RegisterListener($bridge, $state, $listener) if $listener;
    $bridge->{TLS_FINGERPRINT} = $fingerprint;
    HABridge_TransportStatus($bridge, $disabled);
    HABridge_DiagnosticTimer($bridge, AttrVal($bridge->{NAME}, 'memoryDiagnostics', 0));
    return undef;
}

sub HABridge_Listen {
    my ($port) = @_;
    return IO::Socket::INET->new(
        LocalAddr => '0.0.0.0', LocalPort => $port, Proto => 'tcp',
        Listen => 4, ReuseAddr => 1, Blocking => 0,
    );
}

sub HABridge_RegisterListener {
    my ($bridge, $state, $listener) = @_;
    $state->{listener} = $listener;
    # TcpServer_Close in FHEM's fork cleanup also reads PORT for a server socket.
    $bridge->{SERVERSOCKET} = $listener;
    $bridge->{PORT} = $state->{port};
    $selectlist{$state->{listener_key}} = {
        FD => fileno($listener), bridge => $bridge, directReadFn => \&HABridge_Accept,
    };
}

sub HABridge_TransportStatus {
    my ($bridge, $disabled) = @_;
    setNotifyDev($bridge, 'global');
    HABridge_Status($bridge, $disabled ? 'disabled' : 'offline',
        statusReason => $disabled ? 'Disabled by attribute' : 'Waiting for Home Assistant',
        subscribedDefinitions => 0);
}

sub HABridge_StopTransport {
    my ($bridge, $state) = @_;
    my $listener_entry = delete $selectlist{$state->{listener_key}};
    delete $listener_entry->{FD} if $listener_entry;
    my $listener = delete $state->{listener};
    delete @$bridge{qw(SERVERSOCKET PORT)};
    close $listener if $listener;
    HABridge_Close($state->{client}) if $state->{client};
    delete @$state{qw(index index_by_name index_dirty ids)};
}

sub HABridge_Attr {
    my ($action, $name, $attribute, $value) = @_;
    if ($action eq 'del' && !defined $attribute) {
        my $error = HABridge_Attr('del', $name, 'disable');
        return $error if $error;
        HABridge_Attr('del', $name, 'bridgeDiagnostics');
        return HABridge_Attr('del', $name, 'memoryDiagnostics');
    }
    if ($attribute eq 'bridgeDiagnostics') {
        return 'bridgeDiagnostics must be 0 or 1' unless defined($value) && $value =~ /\A[01]\z/;
        my $state = $defs{$name}{helper}{hab};
        if ($state) {
            delete @$state{qw(traffic output_high_water)} if $value && !$state->{diagnostics};
            $state->{diagnostics} = $value;
        }
        return undef;
    }
    return undef unless $attribute eq 'disable' || $attribute eq 'memoryDiagnostics';
    $value = 0 if $action eq 'del';
    my $bridge = $defs{$name};
    if ($attribute eq 'memoryDiagnostics') {
        return 'memoryDiagnostics must be 0 or an interval of 10 to 3600 seconds'
            unless defined($value) && $value =~ /\A\d{1,4}\z/ && ($value == 0 || ($value >= 10 && $value <= 3600));
        HABridge_DiagnosticTimer($bridge, $value);
        return undef;
    }
    return 'disable must be 0 or 1' unless defined($value) && $value =~ /\A[01]\z/;
    my $state = $bridge->{helper}{hab} or return undef;
    return undef if $value == ($state->{disabled} // 0);
    if ($value) {
        $state->{disabled} = 1;
        HABridge_StopTransport($bridge, $state);
    } else {
        my $listener = HABridge_Listen($state->{port});
        return "HABridge: cannot bind TLS port $state->{port}: $!" unless $listener;
        $state->{disabled} = 0;
        HABridge_RegisterListener($bridge, $state, $listener);
    }
    HABridge_TransportStatus($bridge, $value);
    return undef;
}

sub HABridge_Get {
    my ($bridge, undef, $command, @args) = @_;
    return 'Unknown argument ' . ($command // '?') . ', choose one of memory:noArg traffic:noArg'
        unless defined($command) && $command =~ /\A(?:memory|traffic)\z/ && !@args;
    if ($command eq 'traffic') {
        my $state = $bridge->{helper}{hab};
        my $stats = $state->{traffic} // {};
        return join("\n", "outputHighWaterBytes=" . ($state->{output_high_water} // 0),
            "readingFramesSkipped=" . (($state->{client} // {})->{reading_frames_skipped} // 0),
            map { "$_: frames=$stats->{$_}[0] bytes=$stats->{$_}[1]" } sort keys %$stats);
    }
    my $sample = HABridge_MemoryTrend($bridge);
    return join("\n", map { "$_=$sample->{$_}" } sort keys %$sample);
}

sub HABridge_DiagnosticTimer {
    my ($bridge, $interval) = @_;
    my $state = $bridge->{helper}{hab} or return;
    RemoveInternalTimer($bridge, 'HABridge_MemoryTick');
    delete $state->{bridge_memory_baseline} if ($state->{memory_interval} // 0) != $interval;
    $state->{memory_interval} = $interval;
    InternalTimer(gettimeofday() + $interval, 'HABridge_MemoryTick', $bridge, 0) if $interval;
}

sub HABridge_MemorySample {
    my ($bridge) = @_;
    my $state = $bridge->{helper}{hab} // {};
    my $client = $state->{client} // {};
    my %sample = (
        state => $state->{status} // 'unknown',
        listener => $state->{listener} ? 1 : 0,
        client => $state->{client} ? 1 : 0,
        connections => $state->{connections} // 0,
        disconnects => $state->{disconnects} // 0,
        rxBytes => ($state->{rx_bytes} // 0) + ($client->{rx_bytes} // 0),
        txBytes => ($state->{tx_bytes} // 0) + ($client->{tx_bytes} // 0),
        inputBytes => length($client->{input} // ''),
        outputBytes => length($client->{output} // ''),
        subscriptions => scalar keys %{ $client->{subscriptions} // {} },
        readingFilters => 0,
        groups => $client->{group_count} // 0,
        catalogEntries => scalar keys %{ $state->{index} // {} },
        uploadBytes => $client->{attribute_upload} ? $client->{attribute_upload}{offset} : 0,
    );
    my $metadata_bytes = 0;
    for my $name (keys %{ $client->{subscriptions} // {} }) {
        my $sub = $client->{subscriptions}{$name};
        $sample{readingFilters} += keys %{ $sub->{readings} // {} };
        $metadata_bytes += bytes::length($_) for ($name, $sub->{id} // '',
            keys %{ $sub->{readings} // {} }, keys %{ $sub->{events} // {} });
    }
    if (my $index = $state->{index}) {
        $metadata_bytes += bytes::length($_) for keys %$index, values %$index;
    }
    $metadata_bytes += bytes::length($_) for @{ $state->{ids} // [] };
    for my $label (qw(startupSets controlPages)) {
        my $cache = $client->{$label eq 'startupSets' ? 'startup_sets' : 'control_pages'} // {};
        $sample{$label} = scalar keys %$cache;
        $sample{"${label}Bytes"} = 0;
        $sample{"${label}Bytes"} += bytes::length($_->{raw} // '') for values %$cache;
    }
    $sample{bridgePayloadBytes} = $metadata_bytes + $sample{inputBytes} + $sample{outputBytes}
        + $sample{startupSetsBytes} + $sample{controlPagesBytes};
    $sample{bridgePerlBytes} = HABridge_PerlBytes($state) // 'unavailable';
    return \%sample;
}

sub HABridge_PerlBytes {
    my ($state) = @_;
    $hab_has_devel_size //= eval { require Devel::Size; 1 } ? 1 : 0;
    return undef unless $hab_has_devel_size;

    # Measure the live scalar slots, not copies of the strings. Follow only
    # owned plain Perl data, never the link to FHEM or socket/file objects.
    my @owned = map { \$state->{$_} } grep { !ref($state->{$_}) || /\A(?:index|index_by_name|ids|metadata_revision)\z/ } keys %$state;
    my $size = Devel::Size::size($state);
    if (my $client = $state->{client}) {
        push @owned, map { \$client->{$_} }
            grep { !ref($client->{$_}) || /\A(?:subscriptions|startup_sets|control_pages)\z/ } keys %$client;
        $size += Devel::Size::size($client);
        if (my $upload = $client->{attribute_upload}) {
            push @owned, map { \$upload->{$_} } grep { !ref($upload->{$_}) } keys %$upload;
            $size += Devel::Size::size($upload);
        }
    }
    return $size + Devel::Size::total_size(\@owned) - Devel::Size::size(\@owned);
}

sub HABridge_RemoveLegacyMemoryReadings {
    my ($bridge) = @_;
    return unless $bridge->{READINGS};
    delete @{$bridge->{READINGS}}{qw(memoryRssKiB memoryRssPeakKiB memoryProcessFds
        memoryRssGrowthKiB memoryCgroupRootKiB memoryCgroupGrowthKiB)};
}

sub HABridge_MemoryTrend {
    my ($bridge) = @_;
    my $sample = HABridge_MemorySample($bridge);
    my $state = $bridge->{helper}{hab} or return $sample;
    my $now = clock_gettime(CLOCK_MONOTONIC);
    my $baseline = $state->{bridge_memory_baseline} //= {
        time => $now,
        initial => { map { $_ => $sample->{$_} } qw(bridgePayloadBytes bridgePerlBytes) },
        peak => {},
    };
    my $elapsed = $now - $baseline->{time};
    $sample->{sampleSeconds} = int($elapsed);
    for my $metric (qw(bridgePayload bridgePerl)) {
        my $key = "${metric}Bytes";
        my ($previous, $current) = ($baseline->{initial}{$key}, $sample->{$key});
        next unless defined($previous) && defined($current)
            && $previous =~ /\A\d+\z/ && $current =~ /\A\d+\z/;
        my $growth = $sample->{"${metric}GrowthBytes"} = $current - $previous;
        $baseline->{peak}{$key} = $current if !exists($baseline->{peak}{$key}) || $current > $baseline->{peak}{$key};
        $sample->{"${metric}PeakBytes"} = $baseline->{peak}{$key};
        $sample->{"${metric}RateBytesPerHour"} = int(3600 * $growth / $elapsed) if $elapsed >= 60;
    }
    return $sample;
}

sub HABridge_MemoryTick {
    my ($bridge) = @_;
    my $state = $bridge->{helper}{hab} or return;
    my $interval = $state->{memory_interval} or return;
    my $sample = HABridge_MemoryTrend($bridge);
    Log3($bridge->{NAME}, 3, "HABridge $bridge->{NAME}: memory " .
        join(' ', map { "$_=$sample->{$_}" } sort keys %$sample));
    readingsBeginUpdate($bridge);
    readingsBulkUpdate($bridge, 'memorySampleSeconds', $sample->{sampleSeconds});
    readingsBulkUpdate($bridge, $_, $sample->{$_} // 'unavailable') for
        qw(bridgePayloadBytes bridgePayloadGrowthBytes bridgePayloadPeakBytes bridgePayloadRateBytesPerHour
           bridgePerlBytes bridgePerlGrowthBytes bridgePerlPeakBytes bridgePerlRateBytesPerHour);
    readingsEndUpdate($bridge, 0);
    InternalTimer(gettimeofday() + $interval, 'HABridge_MemoryTick', $bridge, 0);
}

sub HABridge_Status {
    my ($bridge, $status, %details) = @_;
    $bridge->{helper}{hab}{status} = $status;
    my $level = $status eq 'error' ? 3 : 4;
    my $reason = $details{statusReason} // 'No reason recorded';
    $reason .= "; $details{lastErrorDetail}"
        if $status eq 'error' && defined($details{lastErrorDetail}) && $details{lastErrorDetail} ne '-';
    Log3($bridge->{NAME}, $level, "HABridge $bridge->{NAME}: $status ($reason)");
    readingsBeginUpdate($bridge);
    readingsBulkUpdate($bridge, 'state', $status);
    readingsBulkUpdate($bridge, $_, $details{$_}) for sort keys %details;
    readingsEndUpdate($bridge, 1);
    $bridge->{STATE} = $status;
}

sub HABridge_Token {
    my ($value) = @_;
    return defined($value) && !ref($value) && $value =~ /\A[A-Za-z0-9_.:-]{1,128}\z/;
}

sub HABridge_Argument {
    my ($value) = @_;
    return HABridge_Token($value) && $value !~ /:/;
}

sub HABridge_Number {
    my ($value) = @_;
    return defined($value) && !ref($value) && length($value) <= 18 &&
        $value =~ /\A-?[0-9]+(?:\.[0-9]+)?\z/;
}

sub HABridge_TlsIdentity {
    my ($port) = @_;
    my $path = AttrVal('global', 'modpath', '.') . "/.habridge-$port.pem";
    if (!-e $path) {
        my $key = IO::Socket::SSL::Utils->can('KEY_create_ec');
        die unless $key;
        my ($cert, $private) = CERT_create(
            key => $key->(), subject => {commonName => 'FHEM HABridge'},
            not_before => time() - 60, not_after => time() + 10 * 365 * 86400,
        );
        my $pem = PEM_cert2string($cert) . PEM_key2string($private);
        CERT_free($cert);
        KEY_free($private);
        sysopen(my $out, $path, O_WRONLY | O_CREAT | O_EXCL, 0600) or die;
        my $written = print {$out} $pem;
        my $closed = close $out;
        if (!$written || !$closed) {
            unlink $path;
            die;
        }
    }
    die if -l $path;
    open my $file, '<:raw', $path or die;
    my @info = stat($file);
    die unless @info && -f _ && !($info[2] & 0077) && $info[7] <= 65536;
    my $size = read($file, my $pem, 65537);
    close $file;
    die unless defined($size) && $size <= 65536;
    my ($base64) = $pem =~ /-----BEGIN CERTIFICATE-----([A-Za-z0-9+\/=\s]+)-----END CERTIFICATE-----/;
    die unless $base64;
    my $tls = IO::Socket::SSL::SSL_Context->new(
        SSL_server => 1, SSL_verify_mode => SSL_VERIFY_NONE,
        SSL_version => 'SSLv23:!SSLv2:!SSLv3:!TLSv1:!TLSv1_1',
        SSL_cert_file => $path, SSL_key_file => $path,
    ) or die;
    return ($tls, sha256_hex(decode_base64($base64)));
}

sub HABridge_Undef {
    my ($bridge) = @_;
    RemoveInternalTimer($bridge, 'HABridge_MemoryTick');
    my $state = delete $bridge->{helper}{hab};
    return undef unless $state;
    HABridge_StopTransport($bridge, $state);
    return undef;
}

sub HABridge_Accept {
    my ($entry) = @_;
    my $bridge = $entry->{bridge};
    my $state = $bridge->{helper}{hab};
    return unless $state && $state->{listener} && !$state->{disabled} && $init_done;
    my $socket = $state->{listener}->accept;
    return unless $socket;
    if ($state->{client} || ($socket->peerhost // '') ne $state->{ha_ip}) {
        close $socket;
        return;
    }
    if (!defined($socket->blocking(0))) {
        close $socket;
        return;
    }
    setsockopt($socket, IPPROTO_TCP, TCP_NODELAY, 1);
    if (!HABridge::Socket->start_SSL($socket, SSL_server => 1,
        SSL_startHandshake => 0, SSL_reuse_ctx => $state->{tls})) {
        close $socket;
        return;
    }
    my $key = "HABridge:" . refaddr($bridge) . ":client";
    my $client = {
        FD => fileno($socket), socket => $socket, key => $key, bridge => $bridge,
        directReadFn => \&HABridge_OnReadable, input => '', output => '', handshaking => 1,
        last_input => clock_gettime(CLOCK_MONOTONIC), subscriptions => {},
    };
    weaken($client->{bridge});
    $state->{client} = $client;
    $bridge->{CD} = $socket;
    ++$state->{connections};
    HABridge_Watch($client);
    InternalTimer(gettimeofday() + 5, 'HABridge_Deadline', $client, 0);
}

sub HABridge_Deadline {
    my ($client) = @_;
    return unless defined $client->{FD};
    if (!$client->{authenticated} || clock_gettime(CLOCK_MONOTONIC) - $client->{last_input} >= 45) {
        my $reason = $client->{authenticated} ? 'No traffic from Home Assistant' : 'Handshake or login timed out';
        HABridge_Close($client, $reason, !$client->{authenticated});
        return;
    }
    my $now = clock_gettime(CLOCK_MONOTONIC);
    delete $client->{attribute_upload} if $client->{attribute_upload}
        && $client->{attribute_upload}{until} < $now;
    for my $cache ($client->{startup_sets}, $client->{control_pages}) {
        next unless $cache;
        delete @$cache{grep { $cache->{$_}{until} < $now } keys %$cache};
    }
    InternalTimer(gettimeofday() + 5, 'HABridge_Deadline', $client, 0);
}

sub HABridge_Close {
    my ($client, $reason, $error, $detail) = @_;
    return unless defined delete $client->{FD};
    delete $client->{attribute_upload};
    delete $selectlist{$client->{key}};
    my $writer = delete $selectlist{"$client->{key}:write"};
    delete $writer->{FD} if $writer;
    RemoveInternalTimer($client);
    my $socket = $client->{socket};
    if ($socket->isa('IO::Socket::SSL')) {
        $socket->close(SSL_no_shutdown => 1);
    } elsif (defined fileno($socket)) {
        close $socket;
    }
    my $bridge = $client->{bridge} or return;
    delete $bridge->{CD} if $bridge->{CD} && $bridge->{CD} == $socket;
    delete $logInform{$bridge->{NAME}};
    my $state = $bridge->{helper}{hab};
    if ($state && $state->{client} && $state->{client} == $client) {
        delete $state->{client};
        ++$state->{disconnects};
        $state->{rx_bytes} += $client->{rx_bytes} // 0;
        $state->{tx_bytes} += $client->{tx_bytes} // 0;
        setNotifyDev($bridge, 'global');
        my %details = (statusReason => $reason // 'Connection closed', subscribedDefinitions => 0);
        $details{lastDisconnected} = TimeNow() if $client->{authenticated};
        if ($error) {
            $details{lastError} = $reason;
            $details{lastErrorAt} = TimeNow();
            $details{lastErrorDetail} = $detail // '-';
        }
        HABridge_Status($bridge, $error ? 'error' : 'offline', %details)
            if !$state->{disabled} && ($client->{authenticated} || $error);
    }
    return;
}

sub HABridge_Queue {
    my ($client, $message) = @_;
    return unless defined $client->{FD};
    my $bytes = eval { $hab_json->encode($message) . "\n" };
    my $queued = length($client->{output});
    if ($client->{reading_batches} && defined($bytes) &&
        ($message->{type} // '') =~ /\Areadings?\z/ &&
        $queued + length($bytes) > HAB_QUEUE_LIMIT - HAB_FRAME_LIMIT) {
        my $stream = $message->{stream};
        ++$client->{reading_frames_skipped};
        return 1 if $client->{reading_gaps}{$stream}++;
        # Let HA repair this stream. Leave room for responses and real events.
        return HABridge_Queue($client, {
            type => 'reading_gap', stream => $stream, seq => $message->{seq},
        });
    }
    if (!defined($bytes) || length($bytes) > HAB_FRAME_LIMIT ||
        $queued + length($bytes) > HAB_QUEUE_LIMIT) {
        HABridge_Close($client, 'Bridge output exceeded its limit', 1);
        return;
    }
    $client->{output} .= $bytes;
    if (my $bridge = $client->{bridge}) {
        my $state = $bridge->{helper}{hab};
        if ($state && $state->{diagnostics}) {
            my $stats = $state->{traffic}{$message->{type} // 'reply'} //= [0, 0];
            ++$stats->[0];
            $stats->[1] += length($bytes);
            my $queued = length($client->{output});
            $state->{output_high_water} = $queued if $queued > ($state->{output_high_water} // 0);
        }
    }
    HABridge_Watch($client);
    return 1;
}

sub HABridge_Watch {
    my ($client) = @_;
    return unless defined $client->{FD};
    my $key = $client->{key};
    if (($client->{wait} // '') eq 'write') {
        delete $selectlist{$key};
    } else {
        $selectlist{$key} = $client;
    }
    if (($client->{wait} // '') eq 'write' ||
        (!$client->{handshaking} && !$client->{wait} && length($client->{output}))) {
        $selectlist{"$key:write"} //= {
            FD => $client->{FD}, client => $client, directWriteFn => \&HABridge_OnWritable,
        };
        # FHEM dispatches readiness by FD. The separate read entry owns all reads.
        # A write entry can see the same readable FD and must not fall back to CallFn.
        $selectlist{"$key:write"}{directReadFn} = \&HABridge_IgnoreReadable;
    } else {
        my $writer = delete $selectlist{"$key:write"};
        delete $writer->{FD} if $writer;
    }
}

sub HABridge_IgnoreReadable { return; }

sub HABridge_OnReadable {
    my ($client) = @_;
    return if ($client->{wait} // '') eq 'write';
    return HABridge_Handshake($client) if $client->{handshaking};
    return HABridge_Write($client) if ($client->{wait} // '') eq 'read';
    return HABridge_Read($client);
}

sub HABridge_OnWritable {
    my ($entry) = @_;
    my $client = $entry->{client};
    return unless defined $client->{FD};
    return HABridge_Handshake($client) if $client->{handshaking};
    return HABridge_Read($client) if ($client->{wait} // '') eq 'write' && !$client->{write_size};
    return HABridge_Write($client);
}

sub HABridge_Handshake {
    my ($client) = @_;
    if ($client->{socket}->accept_SSL) {
        delete @$client{qw(handshaking wait)};
        HABridge_Watch($client);
        HABridge_Pending($client);
    } elsif ($SSL_ERROR == SSL_WANT_READ || $SSL_ERROR == SSL_WANT_WRITE) {
        $client->{wait} = $SSL_ERROR == SSL_WANT_WRITE ? 'write' : 'read';
        HABridge_Watch($client);
    } else {
        HABridge_Close($client, 'TLS handshake failed', 1, HABridge_TlsError());
    }
}

sub HABridge_Write {
    my ($client) = @_;
    my $size = length($client->{output});
    return HABridge_Watch($client) unless $size;
    $client->{write_size} //= $size < HAB_IO_BUDGET ? $size : HAB_IO_BUDGET;
    my $written = $client->{socket}->syswrite($client->{output}, $client->{write_size});
    if (!defined $written) {
        if ($SSL_ERROR == SSL_WANT_READ || $SSL_ERROR == SSL_WANT_WRITE || $! == EINTR) {
            $client->{wait} = $SSL_ERROR == SSL_WANT_READ ? 'read' : 'write';
            return HABridge_Watch($client);
        }
        return HABridge_Close($client, 'TLS write failed', 1, HABridge_TlsError());
    }
    return HABridge_Close($client, 'TLS write returned zero bytes', 1) unless $written;
    $client->{tx_bytes} += $written;
    delete @$client{qw(wait write_size)};
    substr($client->{output}, 0, $written, '');
    delete $client->{reading_gaps} if $client->{reading_gaps} &&
        length($client->{output}) < (HAB_QUEUE_LIMIT - HAB_FRAME_LIMIT) / 2;
    HABridge_Watch($client);
    HABridge_Pending($client);
}

sub HABridge_Pending {
    my ($client) = @_;
    return unless defined($client->{FD}) && !$client->{wait} &&
        !$client->{pending_timer} && $client->{socket}->pending;
    $client->{pending_timer} = 1;
    InternalTimer(gettimeofday() + 0.001, 'HABridge_ReadPending', $client, 0);
}

sub HABridge_ReadPending {
    my ($client) = @_;
    delete $client->{pending_timer};
    HABridge_Read($client) if defined($client->{FD}) && !$client->{wait};
}

sub HABridge_Read {
    my ($client) = @_;
    my $length = $client->{socket}->sysread(my $bytes, HAB_IO_BUDGET);
    if (!defined $length) {
        if ($SSL_ERROR == SSL_WANT_READ || $SSL_ERROR == SSL_WANT_WRITE || $! == EINTR) {
            $client->{wait} = $SSL_ERROR == SSL_WANT_WRITE ? 'write' : undef;
            return HABridge_Watch($client);
        }
        return HABridge_Close($client, 'TLS read failed', 1, HABridge_TlsError());
    }
    return HABridge_Close($client, 'Home Assistant closed the connection') unless $length;
    $client->{rx_bytes} += $length;
    delete $client->{wait};
    $client->{input} .= $bytes;
    return HABridge_Close($client, 'Bridge input exceeded its limit', 1)
        if length($client->{input}) > HAB_FRAME_LIMIT + HAB_IO_BUDGET;
    HABridge_Drain($client) unless $client->{drain_pending};
    HABridge_Watch($client);
    HABridge_Pending($client);
}

sub HABridge_TlsError {
    my $errno = 0 + $!;
    my $error = IO::Socket::SSL::errstr() // '';
    $error =~ s/[\x00-\x1f\x7f]+/ /g;
    my $detail = join(', ', grep { length } ($errno ? "errno=$errno" : '', $error));
    return length($detail) ? substr($detail, 0, 240) : undef;
}

sub HABridge_DeferDrain {
    my ($client, $delay) = @_;
    return unless defined $client->{FD};
    $client->{drain_pending} = 1;
    InternalTimer(gettimeofday() + $delay, 'HABridge_Drain', $client, 0);
}

sub HABridge_Drain {
    my ($client) = @_;
    delete $client->{drain_pending};
    for (1 .. 4) {
        return unless defined $client->{FD};
        my $end = index($client->{input}, "\n");
        return HABridge_Close($client, 'Incoming frame exceeded its limit', 1)
            if $end >= HAB_FRAME_LIMIT ||
            ($end < 0 && length($client->{input}) >= HAB_FRAME_LIMIT);
        return if $end < 0;
        my $line = substr($client->{input}, 0, $end + 1, '');
        my $request = eval { $hab_json->decode($line) };
        if (ref($request) ne 'HASH' || !HABridge_Token($request->{id}) ||
            !HABridge_Token($request->{op})) {
            return HABridge_Close($client, 'Invalid bridge request frame', 1);
        }
        my $started = $client->{last_input} = clock_gettime(CLOCK_MONOTONIC);
        HABridge_Request($client, $request);
        my $elapsed = clock_gettime(CLOCK_MONOTONIC) - $started;
        HABridge_ReportSlowRequest($client, $request, $elapsed) if $elapsed >= HAB_SLOW_REQUEST;
        if (HABridge_YieldAfter($request) || $elapsed >= HAB_REQUEST_YIELD) {
            # Give FHEM's other descriptors and timers a turn, even if the next
            # TLS record arrives before the current input buffer fills again.
            return HABridge_DeferDrain($client, HAB_REQUEST_YIELD);
        }
    }
    HABridge_DeferDrain($client, 0.001) if index($client->{input}, "\n") >= 0;
}

sub HABridge_YieldAfter {
    my ($request) = @_;
    my $op = $request->{op};
    return ($op eq 'describe' && $request->{commands}) ||
        ($op eq 'device_controls' && ($request->{section} // '') ne 'ui') ||
        $op =~ /\A(?:subscribe|subscribe_more|execute|invoke|set_attribute|edit_attribute|attribute_finish|config_save)\z/;
}

sub HABridge_ReportSlowRequest {
    my ($client, $request, $elapsed) = @_;
    my $bridge = $client->{bridge};
    my $state = $bridge->{helper}{hab} or return;
    my $op = $request->{op};
    return unless $op =~ /\A(?:hello|ping|list|describe|read|subscribe|subscribe_more|device_controls|execute|invoke|attributes|set_attribute|edit_attribute)\z/;
    my $name = '-';
    if (HABridge_Token($request->{device}) && (my $device = HABridge_Resolve($state, $request->{device}))) {
        $name = $device->{NAME};
    }
    my $section = $request->{section} // '';
    $section = '' unless $section =~ /\A(?:set|get|attr|ui)\z/;
    my $now = clock_gettime(CLOCK_MONOTONIC);
    my $previous = $state->{slow_request}{$op};
    return if defined($previous) && $now - $previous < 15;
    $state->{slow_request}{$op} = $now;
    return unless $state->{diagnostics};
    Log3($bridge->{NAME}, 3, sprintf(
        'HABridge %s: slow FHEM request op=%s%s device=%s request=%s duration=%.0f ms',
        $bridge->{NAME}, $op, $section ? "/$section" : '', $name, $request->{id} // '-', $elapsed * 1000));
}

sub HABridge_Reply {
    my ($client, $request, %fields) = @_;
    return HABridge_Queue($client, {id => $request->{id}, ok => JSON::PP::true, %fields});
}

sub HABridge_Error {
    my ($client, $request, $code, $message) = @_;
    return HABridge_Queue($client, {id => $request->{id}, ok => JSON::PP::false,
        error => {code => $code, (defined($message) ? (message => $message) : ())}});
}

sub HABridge_Profile {
    my ($device, $sets) = @_;
    my $name = $device->{NAME};
    my @readings = sort keys %{$device->{READINGS} // {}};
    my @attributes = sort keys %{$attr{$name} // {}};
    my %actions;
    if (defined $sets) {
        for my $item (split ' ', $sets) {
            my ($command, $spec) = split /:/, $item, 2;
            next unless HABridge_Argument($command) && $command !~ /\A-/;
            my $id = $command eq 'on' ? 'turn_on' : $command eq 'off' ? 'turn_off' : $command;
            my $no_args = ($spec // '') eq 'noArg' ||
                (!defined($spec) && $command =~ /\A(?:on|off|toggle|stop|open|close)\z/);
            $actions{$id} = {command => $command, arguments => !$no_args};
        }
    }
    return {
        readings => \@readings, events => ['state'], actions => \%actions,
        attribute_names => \@attributes,
    };
}

sub HABridge_Index {
    my ($state) = @_;
    return if exists($state->{index}) && !delete($state->{index_dirty});
    my (%by_id, %duplicate);
    for my $device (values %defs) {
        my $id = $device->{FUUID};
        next unless HABridge_Token($id) && HABridge_Token($device->{NAME}) &&
            HABridge_Token($device->{TYPE}) && $device->{TYPE} ne 'HABridge' &&
            !$device->{TEMPORARY} && !$device->{VOLATILE} && !IsIgnored($device->{NAME});
        $duplicate{$id} = 1 if exists $by_id{$id};
        $by_id{$id} = $device->{NAME};
    }
    delete @by_id{keys %duplicate};
    $state->{index_by_name} = { reverse %by_id };
    $state->{index} = \%by_id;
    $state->{ids} = [sort keys %by_id];
}

sub HABridge_Resolve {
    my ($state, $id) = @_;
    return unless HABridge_Token($id);
    my $name = $state->{index}{$id};
    return unless defined $name;
    my $device = $defs{$name};
    return unless $device && ($device->{FUUID} // '') eq $id &&
        !$device->{TEMPORARY} && !$device->{VOLATILE} && !IsIgnored($name);
    return $device;
}

sub HABridge_Group {
    my ($device, $state) = @_;
    my $type = $device->{TYPE};
    if ($type eq 'CUL_HM') {
        my $parent = $defs{$device->{device} // ''} or return ();
        my $id = $parent->{FUUID};
        return () unless $parent->{TYPE} eq $type && HABridge_Token($id) &&
            ($state->{index}{$id} // '') eq $parent->{NAME};
        return (group => $id, channel => $device->{chanNo});
    }
    if ($type eq 'HMCCUDEV' || $type eq 'HMCCUCHN') {
        my $io = $device->{IODev};
        my $interface = $device->{ccuif};
        return () unless ref($io) eq 'HASH' && HABridge_Token($io->{FUUID}) &&
            HABridge_Token($interface) && ($device->{ccuaddr} // '') =~ /\A([A-Za-z0-9_-]+)(?::([0-9]+))?\z/;
        my ($address, $channel) = ($1, $2);
        return (group => join('/', 'ccu', $io->{FUUID}, $interface, uc($address)), channel => $channel);
    }
    return ();
}

sub HABridge_Text {
    my ($text, $max) = @_;
    return undef unless defined($text) && !ref($text) && length($text) <= $max;
    my $copy = "$text";
    return utf8::is_utf8($copy) ? $copy : decode('UTF-8', $copy);
}

sub HABridge_Reading {
    my ($device, $name) = @_;
    my $reading = $device->{READINGS}{$name};
    return unless $reading;
    my $value = HABridge_Text($reading->{VAL}, 512);
    return unless defined $value;
    my $time = HABridge_Text($reading->{TIME}, 32);
    return {device => $device->{FUUID}, reading => $name, value => $value,
        (defined($time) ? (source_ts => $time) : ())};
}

sub HABridge_ModelReading {
    my ($device) = @_;
    return !$attr{$device->{NAME}}{model} &&
        ($device->{TYPE} eq 'CUL_WS' || $device->{TYPE} eq 'ESA2000');
}

sub HABridge_Request {
    my ($client, $request) = @_;
    my $state = $client->{bridge}{helper}{hab};
    my $op = $request->{op};
    if (!$client->{authenticated}) {
        return HABridge_Close($client, 'Home Assistant authentication failed', 1) unless $op eq 'hello' &&
            HABridge_Token($request->{token}) && length($request->{token}) == length($state->{token}) &&
            ($request->{token} ^. $state->{token}) !~ /[^\x00]/;
        return HABridge_Error($client, $request, 'unsupported_version')
            unless HABridge_Number($request->{version}) && $request->{version} eq '1';
        $client->{authenticated} = 1;
        $client->{reading_batches} = ref($request->{features}) eq 'ARRAY' &&
            grep { defined($_) && !ref($_) && $_ eq 'reading_batches' } @{$request->{features}};
        HABridge_Status($client->{bridge}, 'online', statusReason => 'Authenticated Home Assistant',
            lastConnected => TimeNow(), subscribedDefinitions => 0);
        $state->{epoch} //= sprintf('%d:%.6f', $$, scalar gettimeofday());
        return HABridge_Reply($client, $request, version => 1, server_id => $state->{server_id},
            epoch => $state->{epoch},
            capabilities => [qw(list describe read subscribe subscribe_append subscribe_more subscription_delta catalog_scope reading_batches config_status_push profile_cache attribute_values ha_selection invoke attributes set_attribute device_controls reading_filter device_logs ping paced_requests attribute_editor config_save)]);
    }
    return HABridge_Reply($client, $request) if $op eq 'ping';
    return HABridge_SaveRequest($client, $request, $client->{bridge})
        if $op eq 'config_status' || $op eq 'config_save';
    return HABridge_Unsubscribe($client, $request) if $op eq 'unsubscribe';
    return HABridge_Error($client, $request, 'bad_request')
        unless $op =~ /\A(?:list|describe|read|subscribe|subscribe_more|invoke|attributes|set_attribute|device_controls|execute|edit_attribute|attribute_values|attribute_list|attribute_begin|attribute_chunk|attribute_finish|attribute_abort)\z/;
    HABridge_Index($state);

    if ($op eq 'list') {
        my $offset = $request->{offset} // 0;
        return HABridge_Error($client, $request, 'bad_request') unless
            !ref($offset) && $offset =~ /\A[0-9]{1,8}\z/ && $offset <= @{$state->{ids}};
        return HABridge_Error($client, $request, 'catalog_changed')
            if ($offset || exists $request->{revision}) &&
            (!HABridge_Number($request->{revision}) || $request->{revision} != $state->{revision});
        my @items;
        my $size = 0;
        while ($offset < @{$state->{ids}} && @items < 32) {
            my $id = $state->{ids}[$offset];
            my $device = HABridge_Resolve($state, $id);
            if (!$device) {
                $offset++;
                next;
            }
            my $name = $device->{NAME};
            my %group = HABridge_Group($device, $state);
            my $model = HABridge_Text($attr{$name}{model}, 128);
            if ((!defined($model) || $model eq '') && $device->{TYPE} eq 'CUL_HM' && $group{group}) {
                my $parent = HABridge_Resolve($state, $group{group});
                $model = HABridge_Text($attr{$parent->{NAME}}{model}, 128) if $parent;
            }
            my $item = {
                device => $id, name => $name, type => $device->{TYPE},
                alias => HABridge_Text($attr{$name}{alias}, 128),
                room => HABridge_Text($attr{$name}{room}, 8192),
                model => $model,
                %group,
            };
            if ($device->{TYPE} eq 'FS20' && ($device->{XMIT} // '') =~ /\A[0-9a-f]{4}\z/i &&
                ($device->{BTN} // '') =~ /\A[0-9a-f]{2}\z/i) {
                $item->{address} = lc("$device->{XMIT} $device->{BTN}");
            }
            my $bytes = length($hab_json->encode($item)) + 1;
            last if @items && $size + $bytes > HAB_FRAME_LIMIT - 1024;
            $size += $bytes;
            push @items, $item;
            $offset++;
        }
        return HABridge_Reply($client, $request, revision => $state->{revision}, items => \@items,
            next_offset => $offset < @{$state->{ids}} ? $offset : undef);
    }
    if ($op eq 'subscribe') {
        return HABridge_Subscribe($client, $request, $state);
    }
    my $device = HABridge_Resolve($state, $request->{device});
    return HABridge_Error($client, $request, 'not_allowed') unless $device;
    return HABridge_SubscribeMore($client, $request, $device) if $op eq 'subscribe_more';
    return HABridge_Controls($client, $request, $device, $state) if $op eq 'device_controls';
    if ($op eq 'describe') {
        my $instance = sha256_hex(join(':', $state->{epoch} // '', $device->{NR} // '', refaddr($device)));
        my $revision = HABridge_DeviceRevision($state, $device);
        my $sets;
        if (HABridge_Number($request->{if_revision}) && $request->{if_revision} == $revision) {
            my $reading_schema = sha256_hex(encode('UTF-8', join("\0", sort keys %{$device->{READINGS} // {}})));
            if (($request->{reading_schema} // '') eq $reading_schema &&
                    ($request->{device_instance} // '') eq $instance &&
                    !HABridge_ModelReading($device)) {
                return HABridge_Reply($client, $request, unchanged => JSON::PP::true);
            }
        }
        if ($request->{commands}) {
            $sets = eval { getAllSets($device->{NAME}) } // '';
            HABridge_RememberStartupSets($client, $device, $state, $sets) unless $@;
        }
        my $profile = HABridge_Profile($device, $sets);
        my %actions = map {
            $_ => $profile->{actions}{$_}{arguments} ? {type => 'arguments'} : {}
        } keys %{$profile->{actions}};
        my %group = HABridge_Group($device, $state);
        my $parent = $device->{TYPE} eq 'CUL_HM' && $group{group}
            ? HABridge_Resolve($state, $group{group}) : undef;
        my $model = $parent ? HABridge_Text($attr{$parent->{NAME}}{model}, 128) : undef;
        if ($device->{TYPE} =~ /\A(?:HMCCUCHN|HMCCUDEV)\z/) {
            $model = HABridge_Text($device->{ccutype}, 128);
        }
        return HABridge_Reply($client, $request, device => $device->{FUUID},
            name => $device->{NAME}, type => $device->{TYPE},
            attributes => HABridge_Attributes($device),
            (defined($model) ? (device_model => $model) : ()),
            attribute_names => $profile->{attribute_names}, device_instance => $instance,
            reading_schema => sha256_hex(encode('UTF-8', join("\0", @{$profile->{readings}}))),
            revision => HABridge_DeviceRevision($state, $device),
            readings => $profile->{readings}, events => $profile->{events}, actions => \%actions);
    }
    if ($op eq 'attribute_values') {
        my $names = $request->{attributes};
        return HABridge_Error($client, $request, 'bad_request') if ref($names) ne 'ARRAY' ||
            @$names > 16 || grep { !defined($_) || ref($_) || /[^A-Za-z0-9_.\/-]/ || length($_) > 128 } @$names;
        my $attrs = $attr{$device->{NAME}} // {};
        my %values = map { $_ => HABridge_Text($attrs->{$_}, 1024) } @$names;
        return HABridge_Reply($client, $request, values => \%values);
    }
    if ($op eq 'read') {
        my $requested = $request->{readings};
        return HABridge_Error($client, $request, 'bad_request') unless
            ref($requested) eq 'ARRAY' && @$requested <= 16 &&
            !grep { !defined($_) || ref($_) || length($_) > 128 } @$requested;
        my @items = map { HABridge_Reading($device, $_) // () } @$requested;
        return HABridge_Reply($client, $request, items => \@items);
    }
    return HABridge_ReadAttribute($client, $request, $device) if $op eq 'attributes';
    return HABridge_AttributeList($client, $request, $device, $state) if $op eq 'attribute_list';
    my $subscription = $client->{subscriptions}{$device->{NAME}};
    my $permission = ($op eq 'edit_attribute' || $op =~ /\Aattribute_/ || ($op eq 'set_attribute' && $client->{controls_permissions})) ? 'edit_attributes' :
        $op eq 'execute' && ($request->{kind} // '') eq 'get' ? 'query' : 'writable';
    return HABridge_Error($client, $request, 'not_allowed')
        unless $subscription && $subscription->{$permission} &&
            $subscription->{id} eq $device->{FUUID} && $subscription->{ref} == refaddr($device);
    return HABridge_SetAttribute($client, $request, $device) if $op eq 'set_attribute';
    return HABridge_EditAttribute($client, $request, $device) if $op eq 'edit_attribute';
    return HABridge_AttributeUpload($client, $request, $device) if $op =~ /\Aattribute_/;
    return HABridge_Execute($client, $request, $device) if $op eq 'execute';
    return HABridge_Invoke($client, $request, $device);
}

sub HABridge_DeviceRevision {
    my ($state, $device) = @_;
    my $floor = $state->{metadata_floor} // $state->{revision};
    my $revision = $state->{metadata_revision}{$device->{FUUID} // ''} // $floor;
    if (($device->{TYPE} // '') eq 'CUL_HM' && (my $parent = $defs{$device->{device} // ''})) {
        my $parent_revision = $state->{metadata_revision}{$parent->{FUUID} // ''} // $floor;
        $revision = $parent_revision if $parent_revision > $revision;
    }
    return $revision;
}

sub HABridge_RememberStartupSets {
    my ($client, $device, $state, $raw) = @_;
    return if length($raw) > 4096;
    my $now = clock_gettime(CLOCK_MONOTONIC);
    my $cache = $client->{startup_sets} //= {};
    my $id = $device->{FUUID};
    return unless defined $id;
    if (!exists($cache->{$id}) && keys(%$cache) >= HAB_STARTUP_SET_LIMIT) {
        my ($oldest) = sort { $cache->{$a}{until} <=> $cache->{$b}{until} } keys %$cache;
        delete $cache->{$oldest};
    }
    $cache->{$id} = {raw => $raw, revision => HABridge_DeviceRevision($state, $device), ref => refaddr($device), until => $now + 8};
}

sub HABridge_TakeStartupSets {
    my ($client, $device, $state, $now) = @_;
    return unless $client->{startup_sets} && defined $device->{FUUID};
    my $entry = delete $client->{startup_sets}{$device->{FUUID}} or return;
    return if $entry->{revision} != HABridge_DeviceRevision($state, $device) || $entry->{ref} != refaddr($device) || $entry->{until} < $now;
    return $entry->{raw};
}

sub HABridge_Controls {
    my ($client, $request, $device, $state) = @_;
    my $name = $device->{NAME};
    my $section = $request->{section} // '';
    my $offset = $request->{offset} // 0;
    return HABridge_Error($client, $request, 'bad_request')
        unless $section =~ /\A(?:set|get|attr|ui)\z/ && $offset =~ /\A[0-9]{1,8}\z/;
    return HABridge_Error($client, $request, 'catalog_changed')
        if ($offset || exists $request->{revision}) &&
            (!HABridge_Number($request->{revision}) || $request->{revision} != HABridge_DeviceRevision($state, $device));
    if ($section eq 'ui') {
        my %ui = map { ($_ => HABridge_Text($attr{$name}{$_}, 4096)) } qw(webCmd widgetOverride);
        return HABridge_Reply($client, $request, ui => \%ui, revision => HABridge_DeviceRevision($state, $device));
    }
    my $key = "$name\0$section";
    my $pages = $client->{control_pages} //= {};
    my $now = clock_gettime(CLOCK_MONOTONIC);
    my $page = $pages->{$key};
    if (!$page || $page->{revision} != HABridge_DeviceRevision($state, $device) || $page->{until} < $now) {
        return HABridge_Error($client, $request, 'catalog_changed') if $offset;
        my $raw = eval {
            $section eq 'set' ? (HABridge_TakeStartupSets($client, $device, $state, $now) // getAllSets($name)) :
            $section eq 'get' ? getAllGets($name) : getAllAttr($name);
        };
        return HABridge_Error($client, $request, 'metadata_error') if $@;
        $raw = HABridge_Text($raw // '', 1048576);
        return HABridge_Error($client, $request, 'limit_exceeded') unless defined $raw;
        $page = {raw => $raw, until => $now + 2, revision => HABridge_DeviceRevision($state, $device),
            snapshot => ++$state->{control_snapshot}};
        if (length($raw) > 4096) {
            $page->{until} = $now + 20;
        }
        if (!exists($pages->{$key}) && keys(%$pages) >= 8) {
            my ($oldest) = sort { $pages->{$a}{until} <=> $pages->{$b}{until} } keys %$pages;
            delete $pages->{$oldest};
        }
        $pages->{$key} = $page;
    }
    return HABridge_Error($client, $request, 'catalog_changed')
        if exists($request->{snapshot}) && (!HABridge_Number($request->{snapshot}) ||
            $request->{snapshot} != $page->{snapshot});
    my $raw = $page->{raw};
    return HABridge_Error($client, $request, 'bad_request') if $offset > length($raw);
    my $part = substr($raw, $offset, 4096);
    my $next = $offset + length($part);
    return HABridge_Reply($client, $request, value => $part, revision => HABridge_DeviceRevision($state, $device),
        snapshot => $page->{snapshot},
        next_offset => $next < length($raw) ? $next : undef);
}

sub HABridge_FhemResult {
    my ($client, $request, $kind, $result, $failed) = @_;
    return HABridge_Error($client, $request, 'fhem_error') if $failed;
    my $message = HABridge_Text(substr($result // '', 0, 4096), 4096);
    if (defined($result) && length($result)) {
        return HABridge_Error($client, $request, 'fhem_error', $message) if $kind ne 'get' || $result =~ /\A(?:Unknown argument|Usage:|No get implemented)\b/i;
        return HABridge_Reply($client, $request, status => 'result', result => $message,
            truncated => length($result) > 4096 ? JSON::PP::true : JSON::PP::false);
    }
    return HABridge_Reply($client, $request, status => 'accepted');
}

sub HABridge_Technical {
    my ($device, $command) = @_;
    return $command =~ /\A(?:raw|reset|factoryReset|pair|unpair|regSet|regBulk|saveConfig|fwUpdate|deviceRename|peerBulk|peerSmart|assignHmKey|getRegRaw)\z/i ||
        ($device->{TYPE} // '') =~ /\A(?:CUL|TSCUL|SIGNALduino|HMLAN|HMUARTLGW)\z/i;
}

sub HABridge_TechnicalTarget {
    my ($device, $command, @args) = @_;
    return 1 if HABridge_Technical($device, $command);
    my $name = $device->{NAME};
    my $eventMap = $attr{$name}{eventMap} or return 0;
    # DoSet evaluates dynamic event maps itself. Require technical permission for those maps.
    return 1 if $eventMap =~ /\A\{.*\}\z/s;
    my @target = ReplaceEventMap($name, [$name, $command, @args], 0);
    return defined($target[1]) && HABridge_Technical($device, $target[1]);
}

sub HABridge_Execute {
    my ($client, $request, $device) = @_;
    my ($kind, $command, $arguments) = @{$request}{qw(kind command arguments)};
    my $name = $device->{NAME};
    return HABridge_Error($client, $request, 'invalid_argument')
        unless defined($kind) && $kind =~ /\A(?:set|get)\z/ &&
            defined($command) && !ref($command) && $command =~ /\A[A-Za-z0-9_.][A-Za-z0-9_.%-]{0,127}\z/ &&
            ref($arguments) eq 'ARRAY' && @$arguments <= 256 &&
            !grep { !defined($_) || ref($_) || /[\x00-\x1f\x7f]/ || /\{\(|\[[^\s\]]+:[^\s\]]+\]/ } @$arguments;
    return HABridge_Error($client, $request, 'limit_exceeded')
        if length(encode('UTF-8', join('', @$arguments))) > 16384;
    my $subscription = $client->{subscriptions}{$name};
    return HABridge_Error($client, $request, 'not_allowed')
        if HABridge_Technical($device, $command) && !$subscription->{technical};
    my $raw = eval { $kind eq 'set' ? getAllSets($name) : getAllGets($name) };
    return HABridge_Error($client, $request, 'metadata_error') if $@;
    my %available = map { my ($key, $spec) = split /:/, $_, 2; ($key => $spec // '') }
        split ' ', $raw // '';
    return HABridge_Error($client, $request, 'not_allowed') unless exists $available{$command};
    return HABridge_Error($client, $request, 'catalog_changed')
        if exists($request->{expected_spec}) && (!defined($request->{expected_spec}) ||
            ref($request->{expected_spec}) || $request->{expected_spec} ne $available{$command});
    return HABridge_Error($client, $request, 'invalid_argument')
        if @$arguments && $available{$command} eq 'noArg';
    my @args = map { $unicodeEncoding ? "$_" : encode('UTF-8', "$_") } @$arguments;
    return HABridge_Error($client, $request, 'not_allowed')
        if $kind eq 'set' && !$subscription->{technical} && HABridge_TechnicalTarget($device, $command, @args);
    my $result = eval {
        if ($kind eq 'set') {
            DoSet($name, $command, @args);
        } else {
            # Call the same module function as CommandGet, with the already resolved device.
            local $device->{CL};
            my @params = ($name, $command, @args);
            CallFn($name, 'GetFn', $device,
                $modules{$device->{TYPE}}{parseParams} ? parseParams(\@params) : @params);
        }
    };
    return HABridge_FhemResult($client, $request, $kind, $result, $@);
}

sub HABridge_AttributeBytes {
    my ($value) = @_;
    return utf8::is_utf8($value) ? encode('UTF-8', $value) : $value;
}

sub HABridge_AttributeTag {
    my ($value) = @_;
    return defined($value) ? sha256_hex(HABridge_AttributeBytes($value)) : 'missing';
}

sub HABridge_AttributeList {
    my ($client, $request, $device, $state) = @_;
    my $offset = $request->{offset} // 0;
    my $attributes = $attr{$device->{NAME}} // {};
    my $page = $client->{attribute_list_page};
    if (!$page || $page->{ref} != refaddr($device) || $page->{revision} != HABridge_DeviceRevision($state, $device)) {
        $page = $client->{attribute_list_page} = {ref => refaddr($device), revision => HABridge_DeviceRevision($state, $device),
            names => [sort keys %$attributes]};
    }
    my $names = $page->{names};
    return HABridge_Error($client, $request, 'bad_request')
        unless HABridge_Number($offset) && $offset <= @$names;
    return HABridge_Error($client, $request, 'catalog_changed')
        if $offset && ($request->{revision} // '') ne HABridge_DeviceRevision($state, $device);
    my @items;
    while ($offset < @$names && @items < 2) {
        my $key = $names->[$offset++];
        my $value = $attributes->{$key};
        next if !defined($value) || ref($value);
        my $bytes = length(HABridge_AttributeBytes($value));
        my $preview = $value;
        my $lines = 1 + ($preview =~ tr/\n/\n/);
        my $full = $bytes <= 4096 && $lines <= 8;
        if (!$full) {
            $preview = substr($value, 0, 320);
            $preview =~ s/\A((?:[^\n]*\n){3}).*/$1/s;
        }
        my $text = utf8::is_utf8($preview) ? $preview : eval { decode('UTF-8', $preview, FB_CROAK) };
        push @items, {name => $key, text => $text, bytes => $bytes, lines => $lines,
            complete => $full && defined($text) ? JSON::PP::true : JSON::PP::false};
    }
    return HABridge_Reply($client, $request, items => \@items, revision => HABridge_DeviceRevision($state, $device),
        next_offset => $offset < @$names ? $offset : undef);
}

sub HABridge_AttributeUpload {
    my ($client, $request, $device) = @_;
    my ($op, $key) = @$request{qw(op attribute)};
    my $id = $device->{FUUID};
    if ($op eq 'attribute_begin') {
        my $expected = $request->{expected};
        return HABridge_Error($client, $request, 'bad_request')
            unless defined($key) && !ref($key) && $key =~ m{\A[A-Za-z0-9_./][A-Za-z0-9_./-]{0,255}\z}
                && defined($expected) && !ref($expected) && $expected =~ /\A(?:missing|[a-f0-9]{64})\z/;
        return HABridge_Error($client, $request, 'attribute_changed')
            if $expected ne HABridge_AttributeTag($attr{$device->{NAME}}{$key});
        my $fh = eval { File::Temp->new() };
        return HABridge_Error($client, $request, 'attribute_storage') unless $fh && binmode($fh, ':raw');
        my $upload_id = ++$client->{attribute_upload_id};
        $client->{attribute_upload} = {id => "$upload_id", device => $id, ref => refaddr($device),
            key => $key, expected => $expected, file => $fh, offset => 0,
            until => clock_gettime(CLOCK_MONOTONIC) + 60};
        return HABridge_Reply($client, $request, upload => "$upload_id");
    }

    my $upload = $client->{attribute_upload};
    return HABridge_Error($client, $request, 'attribute_upload_expired')
        unless $upload && $upload->{device} eq $id && $upload->{ref} == refaddr($device)
            && ($request->{upload} // '') eq $upload->{id} && $upload->{until} >= clock_gettime(CLOCK_MONOTONIC);
    if ($op eq 'attribute_chunk') {
        my ($offset, $data) = @$request{qw(offset data)};
        return HABridge_Error($client, $request, 'bad_request')
            unless HABridge_Number($offset) && $offset == $upload->{offset}
                && defined($data) && !ref($data) && length($data) <= 8192 && $data =~ /\A[A-Za-z0-9+\/=]+\z/;
        my $bytes = decode_base64($data);
        if (!print {$upload->{file}} $bytes) {
            delete $client->{attribute_upload};
            return HABridge_Error($client, $request, 'attribute_storage');
        }
        $upload->{offset} += length($bytes);
        $upload->{until} = clock_gettime(CLOCK_MONOTONIC) + 60;
        return HABridge_Reply($client, $request, offset => $upload->{offset});
    }
    delete $client->{attribute_upload};
    return HABridge_Reply($client, $request) if $op eq 'attribute_abort';
    return HABridge_Error($client, $request, 'bad_request')
        unless HABridge_Number($request->{size}) && $request->{size} == $upload->{offset};
    return HABridge_Error($client, $request, 'attribute_storage') unless seek($upload->{file}, 0, 0);
    my $bytes = '';
    while (length($bytes) < $upload->{offset}) {
        my $length = read($upload->{file}, $bytes, $upload->{offset} - length($bytes), length($bytes));
        return HABridge_Error($client, $request, 'attribute_storage') unless $length;
    }
    my $value = eval { decode('UTF-8', $bytes, FB_CROAK) };
    return HABridge_Error($client, $request, 'invalid_argument') if $@;
    return HABridge_EditAttribute($client,
        {%$request, attribute => $upload->{key}, value => $value, expected => $upload->{expected}, remove => JSON::PP::false},
        $device);
}

sub HABridge_SaveStatus {
    my ($bridge) = @_;
    my $enabled = ($attr{$bridge->{NAME}}{allowConfigSave} // '0') eq '1';
    return {dirty => @structChangeHist ? JSON::PP::true : JSON::PP::false,
        can_save => $enabled ? JSON::PP::true : JSON::PP::false,
        save_error => $bridge->{helper}{hab}{save_error}};
}

sub HABridge_ExternalSaveStatus {
    my ($client) = @_;
    delete $client->{save_status_pending};
    return unless defined($client->{FD}) && $client->{authenticated};
    HABridge_PushSaveStatus($client, $client->{bridge});
}

sub HABridge_PushSaveStatus {
    my ($client, $bridge) = @_;
    my $status = HABridge_SaveStatus($bridge);
    my $stamp = HABridge_SaveSignature($status);
    return if defined($client->{save_status}) && $client->{save_status} eq $stamp;
    $client->{save_status} = $stamp;
    HABridge_Queue($client, {type => 'config_status', %$status});
}

sub HABridge_SaveSignature {
    my ($status) = @_;
    return join("\0", $status->{dirty} ? 1 : 0, $status->{can_save} ? 1 : 0, $status->{save_error} // '');
}

sub HABridge_SaveRequest {
    my ($client, $request, $bridge) = @_;
    my $status = HABridge_SaveStatus($bridge);
    if ($request->{op} eq 'config_status') {
        $client->{save_status} = HABridge_SaveSignature($status);
        if ($request->{details}) {
            my @recent;
            for my $change (@structChangeHist) {
                # History may include attribute values and credentials. Return only the context.
                my ($op, $device, $key) = split ' ', $change, 4;
                next unless defined($op) && $op =~ /\A(?:attr|deleteattr|define|modify|delete|rename)\z/;
                push @recent, join(' ', $op, grep { defined($_) && /\A[A-Za-z0-9_.\/-]+\z/ }
                    ($device, $op =~ /attr\z/ ? $key : undef));
                last if @recent >= 100;
            }
            $status->{recent} = \@recent;
        }
        return HABridge_Reply($client, $request, %$status);
    }
    return HABridge_Error($client, $request, 'not_allowed') unless $status->{can_save};
    my $state = $bridge->{helper}{hab};
    local $state->{bridge_save_running} = 1;
    my $result = eval { CommandSave($client, undef) };
    if ($@ || !defined($result) || $result !~ /\A(?:Wrote configuration to [^\r\n]+|Saved configuration to the DB)\z/) {
        $state->{save_error} = HABridge_Text(substr($result // 'FHEM save failed', 0, 2000), 2000)
            // 'FHEM save failed';
    } else {
        delete $state->{save_error};
    }
    $status = HABridge_SaveStatus($bridge);
    $client->{save_status} = HABridge_SaveSignature($status);
    return HABridge_Reply($client, $request, %$status);
}

sub HABridge_EditAttribute {
    my ($client, $request, $device) = @_;
    my ($key, $value, $remove) = @{$request}{qw(attribute value remove)};
    my $name = $device->{NAME};
    return HABridge_Error($client, $request, 'not_allowed')
        if ($device->{TYPE} // '') eq 'HABridge' && defined($key) && !ref($key) && $key eq 'allowConfigSave';
    return HABridge_Error($client, $request, 'not_allowed')
        unless $name =~ /\A[A-Za-z0-9_.][A-Za-z0-9_.-]*\z/ &&
            defined($key) && !ref($key) && $key =~ m{\A[A-Za-z0-9_./][A-Za-z0-9_./-]{0,255}\z};
    my @targets = devspec2array($name, undef);
    return HABridge_Error($client, $request, 'not_allowed')
        unless @targets == 1 && $targets[0] eq $name;
    # CommandAttr validates the attribute against the real device catalogue,
    # including aliases and pattern-based attributes. Deletion only affects
    # the exact verified device and attribute.
    return HABridge_Error($client, $request, 'not_allowed')
        if $remove && !exists $attr{$name}{$key};
    my $guarded = exists $request->{expected};
    return HABridge_Error($client, $request, 'attribute_changed')
        if $guarded && (!defined($request->{expected}) || ref($request->{expected})
            || $request->{expected} ne HABridge_AttributeTag($attr{$name}{$key}));
    return HABridge_Error($client, $request, 'invalid_argument')
        unless JSON::PP::is_bool($remove) && ($remove ||
            (defined($value) && !ref($value) && $value =~ /\S/ && ($guarded || length($value) <= 8192) &&
             $value !~ /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/));
    $value =~ s/\r//g unless $remove;
    $value = encode('UTF-8', $value) if !$remove && !$unicodeEncoding;
    my $result = eval {
        $remove ? CommandDeleteAttr(undef, "$name $key") : CommandAttr(undef, "$name $key $value");
    };
    my $failed = $@;
    return HABridge_FhemResult($client, $request, 'attr', $result, $failed) unless $guarded;
    my $tag = HABridge_AttributeTag($attr{$name}{$key});
    return HABridge_Reply($client, $request, tag => $tag,
        exact => $tag eq HABridge_AttributeTag($remove ? undef : $value) ? JSON::PP::true : JSON::PP::false,
        error_message => $failed ? 'FHEM rejected the attribute change' :
            HABridge_Text(substr($result // '', 0, 2000), 2000));
}

sub HABridge_Attributes {
    my ($device) = @_;
    my %result;
    for my $key (qw(alias room group model subType chanNo)) {
        my $value = HABridge_Text($attr{$device->{NAME}}{$key} // ($key eq "chanNo" ? $device->{chanNo} : undef), 128);
        $result{$key} = $value if defined $value;
    }
    if ($device->{TYPE} eq 'HMCCUCHN' && ($device->{ccuaddr} // '') =~ /:([0-9]+)\z/) {
        $result{chanNo} = "$1";
    }
    return \%result;
}

sub HABridge_ReadAttribute {
    my ($client, $request, $device) = @_;
    my $revision = HABridge_DeviceRevision($client->{bridge}{helper}{hab}, $device);
    my $key = $request->{attribute};
    my $offset = $request->{offset} // 0;
    return HABridge_Error($client, $request, 'bad_request')
        unless defined($key) && !ref($key) && length($key) <= 256 &&
            !ref($offset) && $offset =~ /\A[0-9]{1,8}\z/;
    my $value = $attr{$device->{NAME}}{$key};
    return HABridge_Error($client, $request, 'not_allowed') unless defined $value && !ref($value);
    return HABridge_Error($client, $request, 'catalog_changed')
        if ($offset || exists $request->{revision}) &&
            (!HABridge_Number($request->{revision}) ||
                $request->{revision} != $revision);
    return HABridge_Error($client, $request, 'bad_request') if $offset > length($value);
    my $chunk = substr($value, $offset, 4096);
    my $next = $offset + length($chunk);
    # Unflagged FHEM strings may contain UTF-8 bytes. Keep chunk boundaries byte-exact.
    if (!utf8::is_utf8($value)) {
        return HABridge_Reply($client, $request, encoding => 'base64',
            value => encode_base64($chunk, ''), revision => $revision,
            next_offset => $next < length($value) ? $next : undef,
            (!$offset && $request->{tag} ? (tag => HABridge_AttributeTag($value)) : ()));
    }
    return HABridge_Reply($client, $request, encoding => 'text', value => $chunk,
        revision => $revision,
        next_offset => $next < length($value) ? $next : undef,
            (!$offset && $request->{tag} ? (tag => HABridge_AttributeTag($value)) : ()));
}

sub HABridge_SetAttribute {
    my ($client, $request, $device) = @_;
    my ($key, $value) = @{$request}{qw(attribute value)};
    return HABridge_Error($client, $request, 'not_allowed')
        if ($device->{TYPE} // '') eq 'HABridge' && defined($key) && !ref($key) && $key eq 'allowConfigSave';
    return HABridge_Error($client, $request, 'not_allowed')
        unless defined($key) && !ref($key) && $device->{NAME} !~ /\A-/ &&
            exists($attr{$device->{NAME}}{$key}) && $key =~ m{\A[A-Za-z0-9_./-]{1,128}\z};
    return HABridge_Error($client, $request, 'invalid_argument')
        unless defined($value) && !ref($value) && length($value) && length($value) <= 8192 &&
        $value !~ /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/ && $value =~ /\S/;
    my @targets = devspec2array($device->{NAME}, undef);
    return HABridge_Error($client, $request, 'not_allowed')
        unless @targets == 1 && $targets[0] eq $device->{NAME};
    $value = encode('UTF-8', $value) unless $unicodeEncoding;
    my $result = eval { CommandAttr(undef, join(' ', $device->{NAME}, $key, $value)) };
    return HABridge_Error($client, $request, 'fhem_error') if $@ || (defined($result) && length($result));
    return HABridge_Reply($client, $request, status => 'accepted');
}

sub HABridge_Invoke {
    my ($client, $request, $device) = @_;
    my $sets = eval { getAllSets($device->{NAME}) } // '';
    my $actions = HABridge_Profile($device, $sets)->{actions};
    my $action = HABridge_Token($request->{action}) && $actions->{$request->{action}};
    return HABridge_Error($client, $request, 'not_allowed') unless $action;
    my $args = $request->{args};
    return HABridge_Error($client, $request, 'invalid_argument') unless ref($args) eq 'HASH';
    my @arguments;
    if (keys(%$args) == 1 && exists $args->{value}) {
        @arguments = ($args->{value});
    } elsif (keys(%$args) == 1 && ref($args->{values}) eq 'ARRAY') {
        @arguments = @{$args->{values}};
    } elsif (keys %$args) {
        return HABridge_Error($client, $request, 'invalid_argument');
    }
    return HABridge_Error($client, $request, 'invalid_argument')
        if @arguments > 8 || (@arguments && !$action->{arguments}) ||
            grep { !defined($_) || ref($_) || !m{\A[A-Za-z0-9_.:/#%+,-]{1,128}\z} } @arguments;
    my $subscription = $client->{subscriptions}{$device->{NAME}};
    return HABridge_Error($client, $request, 'not_allowed')
        if $client->{controls_permissions} && !$subscription->{technical} &&
            HABridge_TechnicalTarget($device, $action->{command}, @arguments);
    my @command = ($action->{command}, @arguments);

    # DoSet takes an exact device name and argument list, not a devspec or command chain.
    # Like a local FHEM set, the target module and its triggered rules run synchronously.
    my $result = eval { DoSet($device->{NAME}, @command) };
    return HABridge_Error($client, $request, 'fhem_error') if $@ || (defined($result) && length($result));
    return HABridge_Reply($client, $request, status => 'accepted');
}

sub HABridge_Subscribe {
    my ($client, $request, $state) = @_;
    my $devices = $request->{devices};
    return HABridge_Error($client, $request, 'bad_request')
        unless ref($devices) eq 'ARRAY' && @$devices <= 16 &&
        (!exists($request->{append}) || JSON::PP::is_bool($request->{append}));
    my %permissions;
    for my $key (qw(writable query edit_attributes technical subscribe_logs)) {
        my $ids = $request->{$key} // [];
        return HABridge_Error($client, $request, 'bad_request')
            unless ref($ids) eq 'ARRAY' && @$ids <= @$devices && !grep { !HABridge_Token($_) } @$ids;
        $permissions{$key} = {map { $_ => 1 } @$ids};
    }
    my $filters = $request->{readings};
    return HABridge_Error($client, $request, 'bad_request')
        if defined($filters) && ref($filters) ne 'HASH';
    my $append = $request->{append};
    return HABridge_Error($client, $request, 'bad_request')
        if exists($request->{reset}) && !JSON::PP::is_bool($request->{reset});
    my $replace = $request->{replace};
    return HABridge_Error($client, $request, 'bad_request') if exists($request->{replace}) &&
        (!JSON::PP::is_bool($replace) || ($replace && (!$append || @$devices != 1)));
    my ($existing_name) = $replace ? grep { $client->{subscriptions}{$_}{id} eq $devices->[0] }
        keys %{$client->{subscriptions}} : ();
    my $existing = defined($existing_name) ? $client->{subscriptions}{$existing_name} : undef;
    my $existing_group = $existing ? $existing->{group} : undef;
    my $retained = $request->{retain_readings} // [];
    return HABridge_Error($client, $request, 'bad_request') unless ref($retained) eq 'ARRAY' &&
        !grep { !defined($_) || ref($_) || length($_) > 128 } @$retained;
    return HABridge_Error($client, $request, 'limit_exceeded')
        if $append && !$existing_group && ($client->{group_count} // 0) >= HAB_GROUP_LIMIT;
    my (%subscriptions, @items);
    my $readings = 0;
    my $reset_tail;
    for my $id (@$devices) {
        my $device = HABridge_Resolve($state, $id);
        return HABridge_Error($client, $request, 'not_allowed') unless $device;
        next if exists $subscriptions{$device->{NAME}};
        return HABridge_Error($client, $request, 'bad_request')
            if $append && exists($client->{subscriptions}{$device->{NAME}}) &&
                (!defined($existing_name) || $existing_name ne $device->{NAME});
        my $profile = HABridge_Profile($device);
        my @names = @{$profile->{readings} // []};
        if (defined($filters) && exists $filters->{$id}) {
            my $selection = $filters->{$id};
            return HABridge_Error($client, $request, 'bad_request')
                unless ref($selection) eq 'ARRAY' && @$selection <= HAB_READ_LIMIT &&
                    !grep { !defined($_) || ref($_) || length($_) > 128 } @$selection;
            my %chosen = map { $_ => 1 } @$selection;
            @names = grep { $chosen{$_} } @names;
        }
        my %events = map { $_ => 1 } @{$profile->{events} // []};
        $readings += @names;
        return HABridge_Error($client, $request, 'limit_exceeded') if $readings > HAB_READ_LIMIT;
        my $preserve = $existing && !$request->{reset} && $existing->{ref} == refaddr($device);
        $reset_tail = 1 if $replace && !$preserve;
        my @keep = $preserve ? grep {
            $existing->{readings}{$_} && exists($device->{READINGS}{$_})
        } @$retained : ();
        $subscriptions{$device->{NAME}} = {
            id => $id, ref => refaddr($device), (map { ($_ => delete($permissions{$_}{$id})) } keys %permissions),
            readings => {map { $_ => 1 } @names, @keep}, events => \%events,
            reading_count => scalar keys %{$device->{READINGS} // {}},
        };
        push @items, map { HABridge_Reading($device, $_) // () }
            grep { !$preserve || !$existing->{readings}{$_} } @names;
    }

    return HABridge_Error($client, $request, 'bad_request') if grep { keys %$_ } values %permissions;
    $client->{controls_permissions} = 1 if exists $request->{edit_attributes};

    # No callback can interleave with this bounded snapshot. Later events enter the same FIFO.
    my $group = $existing_group // {stream => 's' . ++$state->{stream_number}, seq => 0};
    my $stream = $group->{stream};
    $_->{group} = $group for values %subscriptions;
    $client->{subscriptions} = {} unless $append;
    delete $client->{subscriptions}{$existing_name} if defined $existing_name;
    @{$client->{subscriptions}}{keys %subscriptions} = values %subscriptions;
    HABridge_ApplySubscriptions($client);
    HABridge_Reply($client, $request, stream => $stream) or return unless $replace;
    HABridge_SnapshotPages($client, $stream, \@items) or return;
    HABridge_Queue($client, {type => 'snapshot_end', stream => $stream, seq => $group->{seq}}) or return;
    return HABridge_Reply($client, $request, stream => $stream, reset => $reset_tail ? JSON::PP::true : JSON::PP::false) if $replace;
    return 1;
}

sub HABridge_Unsubscribe {
    my ($client, $request) = @_;
    my $ids = $request->{devices};
    return HABridge_Error($client, $request, 'bad_request') if ref($ids) ne 'ARRAY' ||
        @$ids > 16 || grep { !HABridge_Token($_) } @$ids;
    my %remove = map { $_ => 1 } @$ids;
    my @names = grep { $remove{$client->{subscriptions}{$_}{id}} } keys %{$client->{subscriptions}};
    delete @{$client->{subscriptions}}{@names};
    HABridge_ApplySubscriptions($client) if @names;
    return HABridge_Reply($client, $request);
}

sub HABridge_ApplySubscriptions {
    my ($client) = @_;
    my %groups = map { $_->{group}{stream} => 1 } values %{$client->{subscriptions}};
    $client->{group_count} = scalar keys %groups;
    if (my $gaps = $client->{reading_gaps}) {
        delete @$gaps{grep { !$groups{$_} } keys %$gaps};
    }
    readingsSingleUpdate($client->{bridge}, 'subscribedDefinitions',
        scalar(keys %{$client->{subscriptions}}), 0);
    my @log_names = sort grep { $client->{subscriptions}{$_}{subscribe_logs} }
        keys %{$client->{subscriptions}};
    if (@log_names) {
        my $names = join('|', map { quotemeta($_) } @log_names);
        $client->{log_pattern} = qr/(?<![A-Za-z0-9_.-])($names)(?![A-Za-z0-9_.-])/;
        $logInform{$client->{bridge}{NAME}} = 'HABridge_Log';
    } else {
        delete $client->{log_pattern};
        delete $logInform{$client->{bridge}{NAME}};
    }
    setNotifyDev($client->{bridge}, join(',', 'global', sort keys %{$client->{subscriptions}}));
}

sub HABridge_SnapshotPages {
    my ($client, $stream, $items) = @_;
    while (@$items) {
        my @page = splice @$items, 0, 16;
        HABridge_Queue($client, {type => 'snapshot', stream => $stream, items => \@page}) or return;
    }
    return 1;
}

sub HABridge_SubscribeMore {
    my ($client, $request, $device) = @_;
    my $subscription = $client->{subscriptions}{$device->{NAME}};
    return HABridge_Error($client, $request, 'not_allowed') unless $subscription &&
        $subscription->{id} eq $device->{FUUID} && $subscription->{ref} == refaddr($device);
    my $selection = $request->{readings};
    return HABridge_Error($client, $request, 'bad_request') unless ref($selection) eq 'ARRAY' &&
        @$selection && @$selection <= HAB_READ_LIMIT &&
        !grep { !defined($_) || ref($_) || length($_) > 128 } @$selection;

    my @items;
    for my $name (@$selection) {
        next if $subscription->{readings}{$name} || !exists $device->{READINGS}{$name};
        $subscription->{readings}{$name} = 1;
        push @items, HABridge_Reading($device, $name) // ();
    }
    my $stream = $subscription->{group}{stream};
    # The reply is queued after the new values. Keep the existing stream sequence.
    HABridge_SnapshotPages($client, $stream, \@items) or return;
    return HABridge_Reply($client, $request, stream => $stream);
}

# FHEM's public logInform hook supplies a formatted line, without its original
# Log3 device argument. Forward only lines naming exactly one subscribed device.
sub HABridge_Log {
    my ($bridge_name, $line) = @_;
    my $state = $defs{$bridge_name}{helper}{hab} or return;
    my $client = $state->{client} or return;
    my $pattern = $client->{log_pattern} or return;
    return unless defined($line) && length($line) <= 8192;
    return if length($client->{output} // '') > HAB_FRAME_LIMIT;
    my $now = int(clock_gettime(CLOCK_MONOTONIC));
    if (($client->{log_second} // -1) != $now) {
        $client->{log_second} = $now;
        $client->{log_count} = 0;
    }
    return if ($client->{log_count} // 0) >= 10;
    my %names = map { $_ => 1 } ($line =~ /$pattern/g);
    return unless keys(%names) == 1;
    my ($name) = keys %names;
    my $subscription = $client->{subscriptions}{$name};
    return unless $subscription && $subscription->{subscribe_logs};
    my $value = HABridge_Text($line, 8192);
    return unless defined $value;
    my $token = $state->{token};
    $value =~ s/\Q$token\E/[redacted]/g if defined($token) && length($token);
    $value =~ s/((?:password|passwd|token|secret|api[_-]?key)\s*[=:]\s*)\S+/${1}[redacted]/ig;
    $client->{log_count}++;
    HABridge_Queue($client, {type => 'log', device => $subscription->{id}, message => $value});
    return;
}

sub HABridge_CatalogChanges {
    my ($bridge, $state, $client, $events) = @_;
    $state->{change_number} //= $state->{revision};
    $state->{metadata_floor} //= $state->{revision};
    my (%devices, %removed, $inventory, $reconcile, $global_controls);
    for my $change (@$events) {
        next unless defined($change);
        my ($op, $name, $argument) = split ' ', $change, 3;
        if ($op =~ /\A(?:INITIALIZED|REREADCFG)\z/) {
            $reconcile = $inventory = 1;
            next;
        }
        next unless defined($name) && $op =~ /\A(?:DEFINED|DELETED|RENAMED|MODIFIED|ATTR|DELETEATTR)\z/;
        my $attribute = (split ' ', $argument // '')[0] // '';
        if ($name eq 'global') {
            $global_controls = 1 if $op =~ /ATTR\z/ && $attribute eq 'userattr';
            next;
        }
        next if $op =~ /ATTR\z/ && $attribute eq 'verbose';
        my $target = $op eq 'RENAMED' ? $attribute : $name;
        my $source = $defs{$target};
        next if $source && ($source->{TYPE} eq 'HABridge' || $source->{TEMPORARY} || $source->{VOLATILE});
        my $previous = $state->{index_by_name}{$name} // ($client && $client->{subscriptions}{$name}
            ? $client->{subscriptions}{$name}{id} : undef);
        my $id = $source ? $source->{FUUID} : $previous;
        next unless HABridge_Token($id);
        my $membership = $op =~ /\A(?:DEFINED|DELETED|RENAMED|MODIFIED)\z/ || $attribute eq 'ignore';
        my $visible = ($source && !IsIgnored($target)) || defined($previous);
        next unless $visible || $attribute eq 'ignore';
        $inventory = 1 if $membership || $attribute =~ /\A(?:alias|room|group|model|subType|chanNo)\z/;
        $removed{$id} = 1 if $op eq 'DELETED';
        my $kind = $membership ? 'definition' : 'metadata';
        $devices{$id} = $kind if !exists($devices{$id}) || $membership;
    }
    return unless $inventory || $global_controls || %devices;
    my $revision = ++$state->{change_number};
    if ($inventory) {
        ++$state->{revision};
        $state->{index_dirty} = 1;
    }
    if ($reconcile || $global_controls) {
        $state->{metadata_floor} = $revision;
        delete $state->{metadata_revision};
    }
    for my $id (keys %devices) {
        if ($removed{$id}) {
            delete $state->{metadata_revision}{$id};
            next;
        }
        $state->{metadata_revision}{$id} = $revision;
    }
    if ($state->{diagnostics}) {
        my @causes = map {
            my ($op, $name) = split ' ', $_, 3;
            join('/', $op, ($defs{$name // ''} // {})->{TYPE} // '-', $name // '-')
        } grep { defined($_) && /\A(?:INITIALIZED|REREADCFG|DEFINED|DELETED|RENAMED|MODIFIED|ATTR|DELETEATTR)\b/ } @$events;
        Log3($bridge->{NAME}, 4, sprintf('HABridge %s: catalog revision=%s inventory=%d reconcile=%d devices=%d causes=%s',
            $bridge->{NAME}, $revision, !!$inventory, !!$reconcile, scalar keys %devices,
            substr(join(',', @causes), 0, 500)));
    }
    return unless $client && $client->{authenticated};
    if ($reconcile || $inventory || $global_controls) {
        HABridge_Queue($client, {type => 'catalog_changed', revision => $revision,
            scope => $reconcile ? 'reconcile' : $inventory ? 'inventory' : 'controls',
            controls => $global_controls ? JSON::PP::true : JSON::PP::false}) or return;
    }
    for my $id (sort keys %devices) {
        HABridge_Queue($client, {type => 'catalog_changed', revision => $revision,
            scope => $devices{$id}, device => $id}) or return;
    }
}

sub HABridge_Notify {
    my ($bridge, $device) = @_;
    my $state = $bridge->{helper}{hab} or return;
    my $client = $state->{client};
    if ($device->{NAME} eq 'global') {
        my $events = deviceEvents($device, 0) // [];
        HABridge_RemoveLegacyMemoryReadings($bridge)
            if grep { defined($_) && /\A(?:INITIALIZED|REREADCFG)\z/ } @$events;
        return if $state->{disabled};
        if ($client && $client->{authenticated} && !$state->{bridge_save_running}
                && !$client->{save_status_pending}
                && grep { defined($_) && /\ASAVE\b/ } @$events) {
            $client->{save_status_pending} = 1;
            InternalTimer(gettimeofday() + 0.01, 'HABridge_ExternalSaveStatus', $client, 0);
        }
        if ($client && $client->{authenticated}
                && grep { defined($_) && /\A(?:SAVE|INITIALIZED|REREADCFG|DEFINED|DELETED|RENAMED|MODIFIED|ATTR|DELETEATTR)\b/ } @$events) {
            HABridge_PushSaveStatus($client, $bridge)
                unless $state->{bridge_save_running} || grep { defined($_) && /\ASAVE\b/ } @$events;
        }
        HABridge_CatalogChanges($bridge, $state, $client, $events);
        return;
    }
    return unless !$state->{disabled} && $client && defined($client->{FD});
    my $subscription = $client->{subscriptions}{$device->{NAME}} or return;
    return unless $subscription->{id} eq ($device->{FUUID} // '') &&
        $subscription->{ref} == refaddr($device) && !IsIgnored($device->{NAME});
    my $count = scalar keys %{$device->{READINGS} // {}};
    if (exists($subscription->{reading_count}) && $subscription->{reading_count} != $count) {
        $subscription->{reading_count} = $count;
        $state->{change_number} //= $state->{revision};
        $state->{metadata_floor} //= $state->{revision};
        my $revision = ++$state->{change_number};
        $state->{metadata_revision}{$subscription->{id}} = $revision;
        HABridge_Queue($client, {type => 'catalog_changed', scope => 'metadata',
            revision => $revision, device => $subscription->{id}}) or return;
    }
    my $events = deviceEvents($device, 1) // [];
    # Bound actual output in HABridge_Queue. The FHEM event count also includes
    # readings outside the subscription and can exceed one snapshot batch.
    my $group = $subscription->{group};
    my (%sent, @readings);
    for my $event (@$events) {
        next unless defined $event;
        my ($key, $value) = split /: /, $event, 2;
        next unless defined $key;
        my $stream = $group->{stream};
        if ($subscription->{readings}{$key} && !$sent{$key}++) {
            my $reading = HABridge_Reading($device, $key);
            if ($reading) {
                push @readings, $reading;
                if (@readings == ($client->{reading_batches} ? 16 : 1)) {
                    HABridge_ReadingFrames($client, $group, \@readings) or return;
                }
            }
        }
        # A repeated button reading is still a distinct trigger, even if its value did not change.
        if (!defined($value) || $subscription->{events}{$key} || !$device->{READINGS}{$key} ||
            $key =~ /\A(?:action|button|trigger|trig_.+|trigLast)\z/i) {
            my $text = HABridge_Text(defined($value) ? $value : $event, 512);
            if (defined $text) {
                HABridge_ReadingFrames($client, $group, \@readings) or return;
                HABridge_Queue($client, {type => 'event', stream => $stream, seq => ++$group->{seq},
                    device => $subscription->{id}, event => 'state', value => $text, raw => HABridge_Text($event, 512)}) or return;
            }
        }
    }
    HABridge_ReadingFrames($client, $group, \@readings);
    return;
}

sub HABridge_ReadingFrames {
    my ($client, $group, $readings) = @_;
    return 1 unless @$readings;
    my %header = (stream => $group->{stream}, seq => ++$group->{seq});
    my $message = @$readings == 1
        ? {type => 'reading', %header, %{$readings->[0]}}
        : {type => 'readings', %header, items => [@$readings]};
    @$readings = ();
    return HABridge_Queue($client, $message);
}

1;


=pod

=item summary Connect Home Assistant to FHEM using authenticated TCP/TLS
=item summary_DE Verbindet Home Assistant und FHEM &uuml;ber authentifiziertes TCP/TLS

=begin html

<a id="HABridge"></a>
<h3>HABridge</h3>
<ul>
  Provides the TCP/TLS endpoint for the FHEM Bridge custom integration in Home
  Assistant. FHEM supplies a device catalogue, readings, events and attributes.
  Home Assistant selects devices and grants Set, Get, attribute and technical
  command permissions per channel. All configured attributes can be read;
  changing attributes requires the corresponding permission.
  TLS socket processing is non-blocking. Device commands and attribute callbacks
  run in FHEM's main loop, just as native FHEM commands do.
  <br><br>
  Requires IO::Socket::SSL and Net::SSLeay with EC certificate support. On Ubuntu,
  install libio-socket-ssl-perl and libnet-ssleay-perl. Devel::Size is optional
  for estimating the memory occupied by the bridge's Perl structures.
  <br><br>
  <a id="HABridge-define"></a>
  <b>Define</b>
  <ul>
    <code>define &lt;name&gt; HABridge &lt;HA-IPv4&gt; &lt;port&gt; &lt;secret&gt;</code><br><br>
    <ul>
      <li>HA-IPv4: allowed IPv4 source address of Home Assistant.</li>
      <li>port: unused TCP port from 1024 to 65535 on the FHEM host.
        The default suggested in HA is 19091.</li>
      <li>secret: 32 to 128 ASCII letters, digits, underscores or hyphens.
        Generate a separate secret in a terminal with
        <code>openssl rand -hex 32</code>. The secret is stored in the definition
        and saved FHEM configuration.</li>
    </ul><br>
    Example:<br>
    <code>define HA_Bridge HABridge 192.0.2.10 19091 &lt;generated-secret&gt;</code><br><br>
    The first definition creates a local certificate and private key in
    <code>.habridge-&lt;port&gt;.pem</code> under global modpath, with permissions
    0600. Keep this file confidential and preserve it to retain the certificate.
    <code>list &lt;name&gt;</code> shows its SHA-256 fingerprint in
    <code>TLS_FINGERPRINT</code>, and the loaded module version in
    <code>MODULE_VERSION</code>.<br><br>
    In HA, add a FHEM Bridge hub using the FHEM address, this port and the same
    secret. Compare the presented fingerprint with TLS_FINGERPRINT before
    confirming. Only one client is accepted at a time. For another FHEM host,
    add another hub in HA; hosts with different IP addresses may use the same
    port. Allow the TCP port from the HA source address in any firewall.
  </ul><br>
  <a id="HABridge-set"></a>
  <b>Set</b>
  <ul>No module-specific Set commands. Home Assistant reconnects automatically
    after a connection loss. Device control is performed through the HA integration.</ul><br>
  <a id="HABridge-get"></a>
  <b>Get</b>
  <ul>
    <li><code>get &lt;name&gt; memory</code><br>
      Samples bridge-owned buffers, subscriptions, caches and their growth,
      peaks and average growth per hour since the measurement baseline.
      Payload sizes are estimates, not the FHEM process or container memory.
      Perl structure estimates require Devel::Size; otherwise those values
      report unavailable. Rates become available after 60 seconds.</li>
    <li><code>get &lt;name&gt; traffic</code><br>
      Shows frame and byte counters by message type, the highest output buffer
      level and skipped reading frames. Counters require bridgeDiagnostics=1.</li>
  </ul><br>
  <a id="HABridge-attr"></a>
  <b>Attributes</b>
  <ul>
    <li><a id="HABridge-attr-disable"></a><code>disable 0|1</code><br>
      Default 0. Value 1 closes the listener and client connection. Value 0
      or deleting the attribute starts the listener again.</li>
    <li><a id="HABridge-attr-allowConfigSave"></a><code>allowConfigSave 0|1</code><br>
      Default 0. Value 1 permits the HA bridge to execute the global FHEM
      save command. This saves all pending FHEM configuration changes,
      including changes made outside HA. Setting an attribute alone does
      not save the configuration to disk.</li>
    <li><a id="HABridge-attr-bridgeDiagnostics"></a><code>bridgeDiagnostics 0|1</code><br>
      Default 0. Enables additional traffic counters and timings. Requests
      taking at least 50 ms are logged at level 3, catalogue diagnostics at
      level 4. Set the attribute to 0 to stop this additional recording.
      Enabling it starts fresh traffic counters.</li>
    <li><a id="HABridge-attr-memoryDiagnostics"></a><code>memoryDiagnostics &lt;seconds&gt;</code><br>
      Default 0 (off). An interval from 10 to 3600 seconds enables periodic
      bridge memory readings and a level 3 log entry. Changing the interval
      resets the trend baseline.</li>
    <li><a href="#verbose">verbose</a>: connection transitions are logged at
      level 4; errors at level 3.</li>
    <li><a href="#readingFnAttributes">readingFnAttributes</a></li>
  </ul><br>
  <b>Readings</b>
  <ul>
    <li><code>state</code>: online, offline, error or disabled.
      <code>statusReason</code> explains the current state.</li>
    <li><code>lastConnected</code>, <code>lastDisconnected</code>: most recent
      authenticated connection and disconnection.</li>
    <li><code>lastError</code>, <code>lastErrorDetail</code>,
      <code>lastErrorAt</code>: most recent recorded connection error and its time.
      A retained error does not mean that the current connection is offline.</li>
    <li><code>subscribedDefinitions</code>: currently subscribed FHEM definitions.</li>
    <li>With memoryDiagnostics: <code>memorySampleSeconds</code> and
      <code>bridgePayloadBytes</code>, <code>bridgePerlBytes</code>, each with
      <code>GrowthBytes</code>, <code>PeakBytes</code> and
      <code>RateBytesPerHour</code> instead of the Bytes suffix.</li>
  </ul>
</ul>

=end html

=begin html_DE

<a id="HABridge"></a>
<h3>HABridge</h3>
<ul>
  Stellt den TCP/TLS-Endpunkt f&uuml;r die benutzerdefinierte Integration FHEM
  Bridge in Home Assistant bereit. FHEM liefert Ger&auml;tekatalog, Readings,
  Ereignisse und Attribute. In HA werden Ger&auml;te ausgew&auml;hlt und Set,
  Get, Attribut&auml;nderungen und technische Befehle je Kanal freigegeben.
  Alle gesetzten Attribute sind lesbar; &Auml;nderungen erfordern die
  entsprechende Freigabe. Die TLS-Socketverarbeitung ist nicht blockierend.
  Ger&auml;tebefehle und Attributfunktionen laufen wie native FHEM-Befehle
  in der FHEM-Hauptschleife.
  <br><br>
  Ben&ouml;tigt IO::Socket::SSL und Net::SSLeay mit Unterst&uuml;tzung f&uuml;r
  EC-Zertifikate. Unter Ubuntu: libio-socket-ssl-perl und libnet-ssleay-perl.
  Devel::Size ist optional f&uuml;r die Sch&auml;tzung der bridgeeigenen
  Perl-Datenstrukturen.
  <br><br>
  <a id="HABridge-define"></a>
  <b>Define</b>
  <ul>
    <code>define &lt;name&gt; HABridge &lt;HA-IPv4&gt; &lt;port&gt; &lt;secret&gt;</code><br><br>
    <ul>
      <li>HA-IPv4: erlaubte IPv4-Quelladresse von Home Assistant.</li>
      <li>port: freier TCP-Port von 1024 bis 65535 auf dem FHEM-Host.
        In HA wird 19091 vorgeschlagen.</li>
      <li>secret: 32 bis 128 ASCII-Buchstaben, Ziffern, Unterstriche oder
        Bindestriche. Ein eigenes Secret im Terminal mit
        <code>openssl rand -hex 32</code> erzeugen. Es steht in der Definition
        und in der gespeicherten FHEM-Konfiguration.</li>
    </ul><br>
    Beispiel:<br>
    <code>define HA_Bridge HABridge 192.0.2.10 19091 &lt;erzeugtes-secret&gt;</code><br><br>
    Beim ersten Define entstehen Zertifikat und privater Schl&uuml;ssel in
    <code>.habridge-&lt;port&gt;.pem</code> unter global modpath, mit Dateirechten
    0600. Datei vertraulich behandeln und erhalten, damit das Zertifikat
    unver&auml;ndert bleibt. <code>list &lt;name&gt;</code> zeigt den
    SHA-256-Fingerabdruck unter <code>TLS_FINGERPRINT</code> und die geladene
    Modulversion unter <code>MODULE_VERSION</code>.<br><br>
    In HA einen FHEM-Bridge-Hub mit FHEM-Adresse, diesem Port und demselben
    Secret hinzuf&uuml;gen. Den angezeigten Fingerabdruck vor der Best&auml;tigung
    mit TLS_FINGERPRINT vergleichen. Es ist jeweils nur ein Client erlaubt.
    F&uuml;r einen weiteren FHEM-Host einen weiteren Hub in HA hinzuf&uuml;gen;
    bei verschiedenen IP-Adressen darf der Port gleich sein. Eine Firewall
    muss den TCP-Port f&uuml;r die HA-Quelladresse freigeben.
  </ul><br>
  <a id="HABridge-set"></a>
  <b>Set</b>
  <ul>Keine modulspezifischen Set-Befehle. HA verbindet sich nach einem
    Verbindungsabbruch automatisch erneut. Ger&auml;te werden &uuml;ber die
    HA-Integration bedient.</ul><br>
  <a id="HABridge-get"></a>
  <b>Get</b>
  <ul>
    <li><code>get &lt;name&gt; memory</code><br>
      Erfasst bridgeeigene Puffer, Abonnements und Caches mit Wachstum,
      Spitzenwerten und durchschnittlichem Wachstum pro Stunde seit der
      Messbasis. Die Nutzdatengr&ouml;&szlig;en sind Sch&auml;tzungen, keine
      FHEM-Prozess- oder Containerwerte. Perl-Strukturgr&ouml;&szlig;en
      ben&ouml;tigen Devel::Size; sonst steht dort unavailable.
      Raten werden nach 60 Sekunden berechnet.</li>
    <li><code>get &lt;name&gt; traffic</code><br>
      Zeigt Nachrichten- und Bytez&auml;hler je Nachrichtentyp, den h&ouml;chsten
      Ausgabepufferstand und ausgelassene Reading-Nachrichten.
      Die Z&auml;hler erfordern bridgeDiagnostics=1.</li>
  </ul><br>
  <a id="HABridge-attr"></a>
  <b>Attributes</b>
  <ul>
    <li><a id="HABridge-attr-disable"></a><code>disable 0|1</code><br>
      Standard 0. Wert 1 schlie&szlig;t Listener und Clientverbindung.
      Wert 0 oder L&ouml;schen des Attributs startet den Listener wieder.</li>
    <li><a id="HABridge-attr-allowConfigSave"></a><code>allowConfigSave 0|1</code><br>
      Standard 0. Wert 1 erlaubt der HA-Bridge das globale FHEM-save.
      Dieses speichert alle ungespeicherten FHEM-Konfigurations&auml;nderungen,
      auch solche au&szlig;erhalb von HA. Das Setzen eines Attributs allein
      speichert die Konfiguration nicht auf die Platte.</li>
    <li><a id="HABridge-attr-bridgeDiagnostics"></a><code>bridgeDiagnostics 0|1</code><br>
      Standard 0. Aktiviert zus&auml;tzliche Verkehrsz&auml;hler und Zeitmessungen.
      Anfragen ab 50 ms werden mit Loglevel 3 protokolliert,
      Katalogdiagnosen mit Loglevel 4. Wert 0 beendet diese Zusatzaufzeichnung.
      Einschalten beginnt mit neuen Verkehrsz&auml;hlern.</li>
    <li><a id="HABridge-attr-memoryDiagnostics"></a><code>memoryDiagnostics &lt;Sekunden&gt;</code><br>
      Standard 0 (aus). Ein Intervall von 10 bis 3600 Sekunden aktiviert
      regelm&auml;&szlig;ige Speicherreadings der Bridge und einen Logeintrag
      mit Loglevel 3. Ein Intervallwechsel setzt die Trendmessbasis zur&uuml;ck.</li>
    <li><a href="#verbose">verbose</a>: Verbindungswechsel mit Loglevel 4,
      Fehler mit Loglevel 3.</li>
    <li><a href="#readingFnAttributes">readingFnAttributes</a></li>
  </ul><br>
  <b>Readings</b>
  <ul>
    <li><code>state</code>: online, offline, error oder disabled.
      <code>statusReason</code> erkl&auml;rt den aktuellen Zustand.</li>
    <li><code>lastConnected</code>, <code>lastDisconnected</code>: letzte
      authentifizierte Verbindung und Trennung.</li>
    <li><code>lastError</code>, <code>lastErrorDetail</code>,
      <code>lastErrorAt</code>: letzter protokollierter Verbindungsfehler
      mit Zeitpunkt. Ein gespeicherter Fehler bedeutet nicht, dass die
      aktuelle Verbindung offline ist.</li>
    <li><code>subscribedDefinitions</code>: aktuell abonnierte FHEM-Definitionen.</li>
    <li>Mit memoryDiagnostics: <code>memorySampleSeconds</code> sowie
      <code>bridgePayloadBytes</code> und <code>bridgePerlBytes</code>, jeweils
      auch mit <code>GrowthBytes</code>, <code>PeakBytes</code> und
      <code>RateBytesPerHour</code> anstelle der Endung Bytes.</li>
  </ul>
</ul>

=end html_DE

=cut
