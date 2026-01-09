---
name: stage2
description: Entry surface extraction (uses Haiku)
---

# /stage2

Entry Surface Extraction

**Model: Use Haiku for this stage.**

## Instructions

Read ai_artifacts/stage1/services.csv (including path aliases).

Create ai_artifacts/stage2/entry_points.csv

Header:
svc_name,entry_type,route,method,handler_file,handler_func,called_funcs,param_sources

Entry types to look for:
| Type      | Look for                                  |
|-----------|-------------------------------------------|
| HTTP      | REST routes, GraphQL, webhooks            |
| QUEUE     | Message queues (RabbitMQ, SQS, Kafka)     |
| SDK       | Library exports, CLI commands             |
| WEBSOCKET | WebSocket handlers, socket.io             |
| GRPC      | Protocol buffer services, gRPC handlers   |
| CRON      | Scheduled jobs, timers, cron expressions  |
| FILE      | File watchers, inotify, fs.watch          |
| STDIN     | CLI stdin input, readline                 |
| EVENT     | Event emitters, pub/sub listeners         |
| IPC       | Inter-process communication, unix sockets |

Rules:
- One row per concrete handler.
- Expand routers into final handlers only.
- HTTP verbs uppercase.
- QUEUE/EVENT use MESSAGE.
- CRON use SCHEDULE.
- Use alias:path format for files.
- param_sources: path, query, body, headers, message, args, stdin, event.
- No auth labels.
- No security language.

CSV only.
Overwrite.
Stop.
