# X

X(原 Twitter)运营工具集。当前版本 **v0.1:安全登录模块 `xlogin`**。

## 方案选型(GitHub 调研结论)

| 方案 | 代表项目 | 结论 |
|---|---|---|
| 账号密码 / Cookie 模拟登录 | [twikit](https://github.com/d60/twikit)、[twscrape](https://github.com/vladkens/twscrape)、[twitter-api-client](https://github.com/trevorhobenshield/twitter-api-client) | 需要保存密码或 `auth_token` cookie;违反 X 使用条款,易触发风控封号;凭据泄露等同账号被接管。**不采用** |
| **官方 OAuth 2.0 Authorization Code + PKCE** | [tweepy `OAuth2UserHandler`](https://github.com/tweepy/tweepy)、[X 官方文档](https://docs.x.com/fundamentals/authentication/oauth-2-0/user-access-token) | 不接触密码;token 有 scope 限制、会过期、可撤销。**采用** |

在 tweepy 实现(S256 PKCE、public/confidential 客户端区分)的基础上,本项目补强了:

- 回环回调服务器:仅绑定 127.0.0.1、校验 `Host` 头(防 DNS rebinding)、只接收一次请求、不回显任何参数、禁缓存/禁 Referrer
- `state` 常量时间比较(防 CSRF);回调里的 `error` 过滤后才进入错误信息
- token 存系统 Keyring(macOS Keychain / Windows Credential Locker / Secret Service);无 Keyring 时必须显式加 `--insecure-file-store` 才会落盘(目录 0700、文件 0600、原子写入、权限被放宽则拒绝读取)
- X 的 refresh token 每次刷新会轮换:刷新后立即原子持久化新 token
- 所有 token 请求禁止跟随重定向(不向跳转目标重放凭据)、带超时;`repr()`/错误信息/日志均不含 token、code、verifier、secret
- `redirect_uri` 校验:非回环地址必须 https
- `logout` 会在 X 侧撤销 access/refresh token,再删除本地副本(撤销失败也会删本地)

## 使用

1. 在 [X Developer Portal](https://developer.x.com/en/portal/dashboard) 创建 App → *User authentication settings* → 开启 **OAuth 2.0**,类型选 *Native App*(public)或 *Web App*(confidential),Redirect URI 填 `http://127.0.0.1:8080/callback`(必须与配置完全一致)。
2. 安装并配置:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env     # 填 X_CLIENT_ID(confidential 还需 X_CLIENT_SECRET);.env 已被 git 忽略
```

3. 命令:

```bash
xlogin login             # 打开浏览器授权,本地回环接收回调
xlogin login --manual    # 无头/远程服务器:打印 URL,授权后把跳转后的完整 URL 粘贴回来
xlogin whoami            # 显示当前账号(token 过期会自动刷新)
xlogin status            # 只看本地 token 状态,不联网
xlogin refresh           # 强制刷新
xlogin logout            # 撤销并删除
```

在代码中使用:

```python
from xlogin import AuthManager, Config
from xlogin.storage import default_store

mgr = AuthManager(Config.from_env(), default_store())
access_token = mgr.get_token().access_token   # 自动刷新
```

## 开发

```bash
ruff check src tests && ruff format --check src tests
pytest -q
```

## 当前限制 / 后续

- 测试覆盖 PKCE(含 RFC 7636 向量)、URL/请求参数、回环服务器、刷新轮换、撤销、存储权限;X 的 HTTP 端点用 mock,**尚未用真实 X 开发者账号做过联调**。
- 免费 API 额度很低(以 X 当前政策为准),发推等能力请按需追加 scope(如 `tweet.write`)。
- 单账号(以 client_id 为 key);多账号和发帖/定时等运营功能是后续版本。
- 请勿提交 `.env`、`tokens.json`;一旦泄露请在 Developer Portal 重置密钥并 `xlogin logout`。
