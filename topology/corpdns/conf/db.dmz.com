@       IN      SOA     ns.dmz.com. root.dmz.com. (
                              2         ; Serial
                          604800         ; Refresh
                           86400         ; Retry
                         2419200         ; Expire
                          604800 )       ; Negative Cache TTL
    ;
@       IN      NS      ns.dmz.com.
@       IN      A       10.0.0.23
ns      IN      A       10.0.0.23
ws1     IN      A       100.0.0.40
fw      IN      A       100.0.0.1
