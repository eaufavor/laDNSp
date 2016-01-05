# laDNSp: Latency-aware DNS proxy
------
### What is laDNSp
laDNSp is a caching DNS proxy which speeds up Internet access by reducing both DNS lookup delay and the communication delay to the resolved servers.

### Why
laDNSp picks the fastest DNS resolver and the fastest server from the resolved IP addresses.

When resolving IP addresses, laDNSp sends simultaneous DNS requests to multiple DNS resolvers and waits for the first response. It replies to users the first response and also records the rest responses for further refinement. Users always get the fastest DNS responses.

Then, laDNSp measures and caches the fastest IP when a domain name is resolved to multiple IP addresses. When users lookup a cached domain name, laDNSp returns the fastest IP for that domain name instantly. Therefore, users are directed to the fastest server.

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

##### CDF of Lokoup delay for uncached(new) DNS records ([how to read CDF](http://ukclimateprojections.metoffice.gov.uk/22619))
![delay](https://raw.githubusercontent.com/eaufavor/laDNSp/master/evaluation/first_lookup_delay.png)

- 93.7% DNS requests can be finished within 30ms.

