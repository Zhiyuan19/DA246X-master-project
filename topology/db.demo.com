@       IN      SOA     ns.demo.com. root.demo.com. (
                              2         ; Serial
                          604800         ; Refresh
                           86400         ; Retry
                         2419200         ; Expire
                          604800 )       ; Negative Cache TTL
    ;
@       IN      NS      ns.demo.com.
@       IN      A       10.0.0.2
ns      IN      A       10.0.0.2
host1     IN      A       10.0.0.1
fweth2     IN      A       10.0.0.3
