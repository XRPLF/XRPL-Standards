<pre>
    xls: 18
    title: Standard For Bootstrapping XRPLD Networks
    description: An experimental procedure to bootstrapping XRP Ledger Network
    author: Richard Holland (@RichardAH)
    proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/42
    created: 2021-03-25
    status: Stagnant
    category: Ecosystem
</pre>

This procedure is experimental and additions amendments or recommendations based on experience to this standard draft are welcome.

### Problem Definition

`Xrpld` / `rippled`[[1]](https://github.com/ripple/rippled) is the software that processes, achieves consensus upon and serves the decentralised public XRP Ledger, as well as numerous other public and private ledgers.

From time to time a decentralised network may stall, fork, or otherwise fail to achieve consensus because of a bug, network instability, unreliable nodes or operators, a deliberate attack, or any combination of these. In this event the bootstrapping procedure to return the network to normal operation is important and should be followed correctly to avoid (further) forks and halts.

### Terminology

`Validator` refers to a rippled instance configured to publish validations of ledgers.
`UNL` refers to a list of validator public keys that the network has collectively agreed are allowed to validate ledgers.
`Node` refers to a validator currently listed in the network's `UNL`.

### Procedure — Cold Start

Cold start describes a situation in which _none_ of the validators in a network are currently running. This situation can arise because they crashed, were terminated automatically or were terminated manually (or any combination of these.)

1. Select a node from your UNL to be the `leader`. The remaining nodes will be referred to as `followers`.
2. On the `leader` run rippled from your terminal in the foreground with the following flags:
   `./rippled --valid --quorum 1 --load`
3. On each follower run rippled from your terminal in the foreground with the following flags:
   `./rippled --net --quorum 1`
4. In a seperate terminal, on each of the `followers` and on the `leader` you may monitor whether or not ledgers are closing correctly using:
   `./rippled ledger closed`
   In particular ensure the ledger index is incrementing and the ledgers are validated.
5. On the `leader` terminate the foreground rippled process. (Ctrl + C)
6. On the `leader` run rippled normally as a daemon.
7. On the `leader` in the second terminal continue to monitor the last closed ledger until validation is consistently achieved, as per 4.
8. Select one `follower` node.
9. Terminate the foreground process on the selected `follower` and start rippled normally.
10. Monitor for LCL validation as per 4.
11. Repeat from step 8 until all nodes are running normally.

### Troubleshooting

Small networks may require the `quorum` size to be permanently overridden for network stability. To do this modify the control script that runs rippled to include `--quorum X` where X is the number of nodes in your UNL less 1.

### Other cases TBD
