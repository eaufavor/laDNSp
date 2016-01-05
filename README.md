# laDNSp: Latency-aware DNS proxy
------
### What is laDNSp
laDNSp is a caching DNS proxy which speeds up Internet access by reducing both DNS lookup delay and the communication delay to the resolved servers.

### Why
laDNSp picks the fastest DNS resolver and the fastest server from the resolved IP addresses.

For DNS lookup, laDNSp sends simultaneous DNS requests to multiple DNS resolvers and wait for the first response. It replies to users the first response but also records the rest responses for further refinement. Users always get the fastest DNS responses.

laDNSp measures and caches the fastest IP if a domain name resolves to multiple IP addresses. When users lookup a cached domain name, laDNSp returns the fastest IP for that domain name instantly. Therefore, users are directed to the fastest server.

### How to use
1. Install laDNSp on your computer or in your local network.
2. Provide laDNSp several candidate DNS resolvers, including you local resolver and public DNS resolvers
3. Run laDNSp, then select laDNSp as the default resolver of your OS.


### Features
- Fast DNS resolving
- Permanent caching
- Smart IP selection

### Installation & usage

TDB

### Performance tests

TDB
