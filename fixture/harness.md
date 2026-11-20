# Harness

A build gives these controls to an adapter. The controls let an adapter make a
run repeat exactly. They show nothing that a user cannot perceive, except the
request log.

```text
HAR-1 Profile. The adapter names a profile of `service.json` at the start. The default is "default".
HAR-2 Start address. The adapter gives the address at which the build starts.
HAR-3 Clock. In harness mode the clock moves only when the adapter advances it by a number
  of ms. The build runs each timer that becomes due, in order of due time. When the advance
  returns, the build shows the result.
HAR-4 Request log. The adapter can read the list of requests: operation and time in ms from the start.
HAR-5 Reload. The adapter can reload the build. A reload starts the service double and the
  clock again from the fixture.
HAR-6 The build reads time and sets timers only through the clock.
```

The modality sheet of each stack says how a build gives these controls.
