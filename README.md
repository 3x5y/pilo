Vibe-coding a personal information management system.

## Setup

I use LXD on ubuntu to provide a light QEMU VM without the headache.

### 1. Install and initialise LXD

```bash
snap install lxd
lxd init
```

#### 1a. Disable annoying IPv6

```bash
lxc network set lxdbr0 ipv6.nat false
lxc network set lxdbr0 ipv6.address none
```

### 2. Create the VM

```bash
lxc init --vm ubuntu:25.10 pilodev0
lxc config set pilodev0 limits.cpu 4
lxc config set pilodev0 limits.memory 8GiB
lxc config device add pilodev0 src disk source=$(realpath $PWD) path=/src
lxc start pilodev0
```

### 3. Setup the VM
```bash
lxc exec pilodev0 --cwd /src -- sh ./init.sh
```

### 4. Run the tests
```bash
lxc exec pilodev0 --cwd /src -- sh ./test.sh
```


## Notes

What I did:

* Added vibe-drafted specification.md
* Added chat.md
* Setup LXD
* Added first failing tests
* Added init.sh
* Added setup, teardown, runner and capture implementation
* Corrected tests now pass
* Added tests, improved test harness
* POSIX shell compat

