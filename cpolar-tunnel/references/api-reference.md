# cpolar API 参考

## 基础信息

### 认证方式

使用authtoken进行认证，配置后存储在本地配置文件中。

### 获取authtoken

访问 https://dashboard.cpolar.com/auth 登录后获取

## 本地命令接口

### 1. 检查版本

```bash
cpolar version
```

### 2. 配置authtoken

```bash
cpolar authtoken <authtoken>
```

### 3. 获取隧道状态

```bash
cpolar status
```

### 4. 创建HTTP隧道

```bash
cpolar http <local-port>
cpolar http -subdomain=<subdomain> <local-port>
cpolar http -hostname=<domain> <local-port>
```

### 5. 创建TCP隧道

```bash
cpolar tcp <local-port>
cpolar tcp -remote-addr=<port> <local-port>
```

### 6. 创建FTP隧道

```bash
cpolar ftp <local-port>
```

### 7. 创建TLS隧道

```bash
cpolar tls <local-port>
```

### 8. 服务管理

```bash
cpolar service install
cpolar service start
cpolar service stop
cpolar service uninstall
```

## 配置文件格式

### 路径

- Windows: `C:\Users\<username>\.cpolar\cpolar.yml`
- Linux/macOS: `~/.cpolar/cpolar.yml`

### 示例配置

```yaml
authtoken: your-authtoken-here

tunnels:
  http-tunnel:
    addr: 8080
    proto: http
    subdomain: myapp

  tcp-tunnel:
    addr: 22
    proto: tcp
```

## 常见问题

### Q: 登录数超过限制怎么办？

A: 访问 https://dashboard.cpolar.com/status 查看在线设备，或重置authtoken

### Q: 如何重置authtoken？

A: 登录 https://dashboard.cpolar.com/ 用户设置页面，点击重置authtoken

### Q: 配置文件中的authtoken如何移除？

A: 编辑配置文件，删除authtoken行，然后重启cpolar服务