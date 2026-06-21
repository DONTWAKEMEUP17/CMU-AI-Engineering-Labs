# 03 · Redis 主从 — 单线程事件循环 + 异步复制

> **本章核心问题**：Redis 单线程为什么能扛十万 QPS？master 挂了怎么办？复制是同步还是异步、丢数据怎么办？读写分离听起来美好，背后有什么暗坑？
>
> **跟 [[01 Kafka]] 的对照**：Kafka 追求**写吞吐**（顺序追加 log，多 partition），Redis 追求**读吞吐**（一个 master 写、N 个 slave 读）。同样是"分布式"，解决的痛点完全不同 —— 本章末尾会把这条对照线收口。

## 1. Motivation —— 单台 Redis 的两个真实瞬间

回到一个常见的小公司架构：MySQL 在后面、Redis 在前面挡读流量、单台部署、月活几百万、平时岁月静好。

### 瞬间 A：凌晨 3 点的电源故障

那台 Redis 物理机掉电。整个缓存层瞬间归零。

下一秒发生什么？所有原本应该命中缓存的请求全部 miss，**直接打到 MySQL**。MySQL 单库平时被 Redis 挡了 95% 的读流量，现在突然要扛全部 —— CPU 100%，连接池打爆，慢查询堆积，**全站雪崩**。等运维 30 分钟后赶到机房启备机，新闻已经上了。

这是**痛点 #1：单点故障 → 业务死**。

### 瞬间 B：周年大促开场那一秒

首页商品详情接口平时 QPS 5 万，Redis 单机轻松。大促开场那一秒突然涌进来 50 万 QPS。

Redis 是单线程的。它能扛多少？官方 benchmark 8-10 万 QPS 量级，**单机物理上限就在那**。再多就开始排队、超时、雪崩。你不能再加一台 Redis 让它分担 —— 加了第二台，数据不一样，一半用户读不到。

这是**痛点 #2：读流量打不住单机 QPS**。

### 主从复制要解决的就是这两件事

- **痛点 #1（HA）**：搞一个 slave 在旁边实时同步数据，master 一挂，slave 立刻顶上 → 业务不中断
- **痛点 #2（读扩展）**：搞 N 个 slave，写还是只写 master，但读可以分散到所有 slave → 读 QPS 翻 N 倍

> 还有一个**痛点 #3：数据量超过单机内存 / 写 QPS 顶不住单线程**。主从**解决不了** —— master 还是单点写、单机存。这个要靠**Cluster 分片**，本章末尾会展开"什么时候该升级"。

记住这三个痛点的分工，下面所有机制都是为它们服务的。

## 2. 为什么 Redis 单线程也能扛十万 QPS

很多人第一次听 "Redis 单线程"会觉得不可思议 —— 不是说单线程不行才发明多线程的吗？

要理解这点，得先看 Redis 把什么做对了：

### 三件事一起成立才有"单线程也快"

**(1) 数据在内存**
读写完全不需要等磁盘 IO。内存访问大约是磁盘随机读的 **10 万倍**快。绝大多数数据库的瓶颈是 IO 等待，Redis 把这个瓶颈直接绕过去了。

**(2) IO 多路复用（epoll / kqueue）**
单线程的"线程"指的是**执行命令的线程**只有一个。但网络 IO 不是阻塞的 —— Redis 用 epoll 同时监听几万个客户端 socket，谁就绪了 epoll 一次性告诉它，它再一个一个处理：

```c
while (true) {                    // 事件循环
    events = epoll_wait(sockets); // 一次阻塞等多个 fd
    for (event in events) {       // 只处理就绪的
        if (event.readable) handle_read(event.fd);
        if (event.writable) handle_write(event.fd);
    }
}
```

没有就绪的 socket 不会拖慢任何东西。这跟"传统多线程 = 一个线程死等一个连接"完全不同。

**(3) 没有上下文切换、没有锁**
多线程程序的隐藏开销：CPU 在线程之间切换要保存/恢复寄存器和栈（context switch 大约 1-5μs），多线程访问共享数据要加锁解锁。Redis 单线程把这两个开销**全部归零**。

### 单线程的代价：慢命令拖死全场

这一切的代价是 **任何一个慢命令都会卡住整个 Redis**。`KEYS *` 在 100 万 key 上跑一次要几秒钟，这几秒钟所有其他客户端的请求全部排队等待 —— 包括你的核心业务。生产环境的 Redis 配置里要**禁用 KEYS / FLUSHDB / 复杂的 LUA 脚本**，原因就是这。

> 这其实给读写分离埋了个伏笔 —— 后面会提到的"复制延迟"问题，根因之一就是 master 单线程在做别的事时，复制流也跟着堵。

### Redis 6.0 引入多线程 ≠ 命令执行多线程

Redis 6.0 加了"多线程 IO"，**但只是把 socket 读写解析的部分并行了**，真正执行命令的还是单线程。这是为了在万兆网卡下让网络解析不要成为瓶颈，**核心模型没变**。

## 3. 主从复制是怎么动起来的

slave 启动时连上 master，要让自己的数据和 master 一致 —— 怎么做？

### 两阶段：全量 + 增量

**阶段一：全量同步（snapshot）**

1. slave 喊：`PSYNC ? -1`（我是新来的，给我一份完整数据）
2. master 在后台执行 `BGSAVE`，把当前所有内存数据 dump 成一个 **RDB 文件**（二进制快照）
3. master 把 RDB 文件传给 slave
4. slave 清空自己的内存，加载 RDB → 此刻 slave 的数据 = master 在 BGSAVE 那一瞬间的数据

**阶段二：增量复制（command stream）**

阶段一开始的那一瞬到现在，master 又收到了一堆新的写命令（SET / DEL / LPUSH...）。这些命令 master 全部记到一个**环形缓冲区**（`repl_backlog`）里。

5. RDB 同步完后，master 把缓冲区里"BGSAVE 之后的命令"全部推给 slave
6. slave 一条条 replay，追上 master
7. 之后只要有新写命令，master 就**实时**把命令推一份给 slave 的复制连接

到这一步两边就是"数据一致 + 持续同步"的状态了。

### 一个绝妙的设计对偶

把这套机制和 Redis 的**持久化机制**对比一下：

| 机制 | 全量 | 增量 |
|---|---|---|
| **持久化（单机数据落盘）** | RDB 快照 | AOF append-only log |
| **复制（多机数据同步）** | RDB 快照 | 复制命令流 |

**这不是巧合**。"先做一次完整 snapshot、之后只追加增量"这个思想是分布式系统里通用模式，第 04 章 MySQL 复制走的是**全量 dump + binlog 增量**，本质完全一样。包括 [[01-kafka-pub-sub]] 里 Kafka 新 consumer "从 earliest 开始读 → 实时跟上 latest" 也是这个套路。

> 这套套路有个统一名字叫 **log shipping**，业界普及到几乎所有 DB。

## 4. 同步还是异步？Redis 默认是异步

写到 master 之后，master 什么时候算"写成功"？三种选择：

| 模式 | master 什么时候返回 OK | 代价 | 好处 |
|---|---|---|---|
| **同步复制** | 等所有 slave 都确认收到 | 写延迟 = master 延迟 + 最慢 slave 的延迟 | 0 数据丢失 |
| **半同步** | 等 ≥ 1 个 slave 确认 | 写延迟稍涨 | 大概率不丢 |
| **异步复制** | master 写完自己内存就立刻 OK | 几乎无延迟 | master 突然挂可能丢几毫秒数据 |

**Redis 默认走异步**。原因是 Redis 的核心定位是"高速缓存" —— 你要的是**写延迟 < 1ms**。如果非要等 slave 确认，写延迟变成 5-50ms（看 slave 离 master 多远），单机 QPS 直接跌 10 倍。**这违背了 Redis 存在的意义**。

### 异步的代价

- **数据丢失窗口**：master 写完返回 OK 后、命令还没推给 slave 之前，master 挂了 → 那条数据**永久消失**。窗口通常几毫秒到几百毫秒
- **复制延迟（lag）**：slave 永远比 master "晚一点"。这就是后面读写分离里 "read-your-writes" 问题的根因
- **网络分区下脑裂**：master 和 slave 之间网断了，master 还在收写、slave 自己被选成新 master 也在收写 → 网恢复后两边数据冲突，至少一边的写要丢

### Redis 给的"半同步"逃生口

如果你这套 Redis 真的不能丢数据（比如做了**会话存储**、用户掉登录就报警），可以**手动开半同步**：

```
# 配置：至少要有 1 个 slave 在 10 秒内确认，否则 master 拒绝写
min-replicas-to-write 1
min-replicas-max-lag  10
```

或者业务代码里在关键写之后调一次：

```
WAIT 1 100   # 阻塞最多 100ms，等至少 1 个 slave 同步完
```

代价是写延迟从 1ms 涨到 5-50ms。

### 这跟 [[01-kafka-pub-sub]] 里的 acks 完全是同一回事

```
Kafka acks=0     ≈ Redis 异步     ← 不等任何确认
Kafka acks=1     ≈ Redis 异步     ← 等 leader 确认（leader 自己写到 page cache）
Kafka acks=all   ≈ Redis WAIT     ← 等所有/N 个 ISR 确认
```

**"一致性 vs 延迟"的权衡在任何分布式存储里都长一个样**。区别只在默认值 —— Kafka 默认 `acks=1`（折中），Redis 默认 `0`（极致延迟），传统数据库默认同步（极致一致）。**这是产品定位决定的**。

## 5. master 挂了谁来 failover

异步复制说完了，回到痛点 #1：master 真挂了，怎么自动把 slave 顶上去（"failover"）？

业界历史上出现过五种方案，Redis 现在主流是其中两种：

| 方案 | 谁来判断 master 死了 | 谁来执行切换 | 评价 |
|---|---|---|---|
| **A. 客户端自己 ping** | 每个业务方各自 ping | 各自重连 slave | **反面教材** —— 10 个服务 10 套实现，判断不一致 → 脑裂 |
| **B. master 自己发遗言** | master | 自己声明下线 | **物理不可能** —— 真挂了哪还有机会发消息 |
| **C. 外部独立看门狗** | 独立的 Sentinel 集群 | Sentinel 选 leader 来切 | **Redis Sentinel**（2012 上线，2.8 起稳定） |
| **D. 节点之间 gossip** | Cluster 节点互相心跳 + 主观/客观下线判定 | Cluster 内部投票 | **Redis Cluster**（2015 上线） |
| **E. 人工运维** | 监控告警 → 人 | 人 SSH 上去操作 | 5-30 分钟级停服，**只适合不在乎可用性的业务** |

### HA = High Availability，量化标准

主从 + 自动 failover 解决的本质是把"挂掉的时长"压短。业界用"几个 9"衡量：

| 几个 9 | 一年宕机时长 | 什么水平 |
|---|---|---|
| 99%（两个 9） | 87.6 小时 | 个人博客 |
| 99.9%（三个 9） | 8.76 小时 | 普通内网服务 |
| 99.99%（四个 9） | 52 分钟 | 多数互联网业务的及格线 |
| 99.999%（五个 9） | 5.26 分钟 | 银行核心 / 电信 |

人工 failover（方案 E）= 一次故障烧掉 30 分钟，一年故障 5 次直接跌出 4 个 9。Sentinel / Cluster 把切换时间压到 30 秒以内 → 4 个 9 起步。

### Sentinel vs Cluster 真正的设计分歧

为什么 Redis 同时保留两个方案？因为**解决的痛点范围不同**：

| 维度 | Sentinel（方案 C） | Cluster（方案 D） |
|---|---|---|
| **解决哪些痛点** | #1 HA + #2 读扩展 | #1 + #2 + **#3 数据/写扩展** |
| **数据模型** | 一个 master，一份完整数据 | 16384 个 slot，数据分片到多个 master |
| **客户端复杂度** | 客户端连 Sentinel 问"现在 master 是谁" | 客户端要懂 CRC16 算 slot |
| **运维成本** | 多部署 3 个 Sentinel 进程 | 整个拓扑变 Cluster |
| **典型场景** | 单库装得下、只是想要 HA | 数据量 > 单机内存，或 写 QPS > 10w |

业务侧的决策线：

- 数据 < 单机内存（64GB 量级），QPS < 10 万 → **Sentinel 够了**
- 数据 > 单机内存（要存 1TB），或写 QPS > 10 万 → **必须 Cluster**

### Sentinel 自己也是 Raft 集群

一个容易被忽略的事实：Sentinel 通常**部署 3-5 个进程**，它们之间也要选 leader 来执行 failover —— 用的是 **Raft 算法**。所以"用 Sentinel 监控 Redis 主从"本质是 **Raft 集群（Sentinel）在守护 Replication 集群（Redis）**。

这给 [[02-resilientdb-bft]] 章节留了个钩子：当连"看门狗"自己都可能作恶时，Raft 就不够了，得换 PBFT。

## 6. Cluster 分片是怎么切的（本章只做预览）

Cluster 的完整机制留给后面专门讲。这里只把**最核心的 slot 切片**抓出来，方便理解 Sentinel ↔ Cluster 的分界。

### Slot 切片 = 一致性哈希思想的工业实现

Cluster 把整个 key 空间预先切成 **16384 个虚拟槽（slot）**，每个 key 用 `CRC16(key) mod 16384` 算出归属哪个 slot，每台 master 负责其中一段连续 slot：

```
3 台 master 的分配：
  Master A: slot 0     ~ 5460
  Master B: slot 5461  ~ 10922
  Master C: slot 10923 ~ 16383

来一个 SET user:1000 "yang":
  CRC16("user:1000") mod 16384 = 15565
  slot 15565 ∈ [10923, 16383]
  → 直接路由到 Master C
```

### 为什么不直接 `hash(key) mod 节点数`

**因为节点数会变**。直接 `mod 3` 然后加一台变成 `mod 4` —— 几乎所有 key 的归属都会变 → 全集群数据大迁移。

`mod 16384` 是固定的，**加节点只需要把一部分 slot 整段搬走**：原本 3 台变 4 台，只搬 1/4 的 slot，其他 3/4 的 key 完全不动。

### 一个生产小坑：multi-key 命令的 hash tag

`MGET user:1 user:2 user:3` 可能落到 3 个 slot → Cluster 报 `CROSSSLOT` 拒绝。解决方法是 **hash tag**：

```
key 写成 {user}:1, {user}:2, {user}:3
Cluster 只对大括号里的 "user" 算 CRC16
→ 强制让这几个 key 落到同一 slot → 同一 master
```

电商常用 `{order:1000}.items`、`{order:1000}.payment` —— 一个订单的所有数据强制同机，方便批量操作。

## 7. 读写分离的隐藏暗坑

回到主从，最常见的用法是"写打 master、读分散到 slave"，听起来美好 —— 但有两个生产里反复踩的坑。

### 坑 1：read-your-writes 失败

```
t=0ms   用户 POST /profile { nickname: "新昵称" }   → master
t=1ms   服务端返回 200
t=2ms   前端立刻 GET /profile  → slave 1
t=2ms   slave 1 还没同步到 → 返回旧昵称
```

用户体感是 **"我明明改了，怎么还是老的？"** —— 心智模型崩坏。

**解法**：业务方判断"刚写过的 key 在 X 秒内必须读 master"。或者用 `WAIT 1 100` 强制等同步完。

### 坑 2：slave 复制延迟突然飙高

正常 lag < 10ms。但下面这些事一发生 lag 立刻飙到几秒甚至几分钟：

- master 跑了一个慢命令（`KEYS *`、`SORT` 大集合）→ 单线程被卡 → 复制流也卡
- 网络抖动 → 命令积压
- slave 自己在做 RDB save → 复制 buffer 涨
- 突发大 key 写入 → 一个 key 几十 MB 推过去要一秒

应对：**监控复制延迟（`INFO replication` → `master_repl_offset` vs `slave_repl_offset` 差值）**，告警阈值通常 1-5 秒。

### 业务侧怎么决定哪些读走 slave

按"能不能容忍 stale read"分类：

| 业务场景 | 走 master 还是 slave | 原因 |
|---|---|---|
| 商品详情页 | slave | 商品信息几小时改一次，stale 1 秒无感 |
| 用户刚提交订单后查订单详情 | **master** | read-your-writes，stale 会让用户怀疑没下单成功 |
| 后台运营看报表 | slave | 几秒延迟无所谓 |
| 库存扣减后展示库存 | **master** | 超卖风险 |
| Feed 流（看别人发的内容） | slave | 自己看不到自己刚发的内容是可接受的 |

## 8. 一句话收口

> **Redis 主从 = 内存数据库的"HA + 读扩展"方案**。用 RDB + 命令流做异步复制，靠 Sentinel 做自动 failover。**牺牲了强一致换延迟**，所以默认丢一点点数据是产品定位决定的，不是 bug。**数据量或写 QPS 顶到单机上限**时，要升级到 Cluster 做分片。

### 跟其他章节的对照

- **vs [[01-kafka-pub-sub]]**：Kafka 用 partition + replication 解决**写扩展**，Redis 主从用同样的"leader + follower"模型解决**读扩展**。同一个分布式套路，方向相反。两边的"acks / WAIT" 是平行设计。
- **vs [[02-resilientdb-bft]]**：Redis 主从假设节点 honest（crash-recovery 模型），节点崩了走 failover 就够。BFT 假设节点可能恶意，failover 要走多轮共识 —— 复杂度高一个量级，吞吐低两个量级。
- **vs [[04-mysql-replication]]**：MySQL 走的是 binlog 复制，跟 Redis 的"RDB + 命令流"是同一个 log shipping 套路。但 MySQL 持久化是必须的（磁盘 DB），主从场景下更在意**一致性**而非延迟，所以默认半同步、丢数据的接受度比 Redis 低。

下一站可以是 [[02-resilientdb-bft]]（信任模型完全不同的另一条路）或 [[04-mysql-replication]]（同样思想在磁盘 DB 上的不同权衡）。
