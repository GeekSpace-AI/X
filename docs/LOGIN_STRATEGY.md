# 登录策略(决策记录)

日期:2026-10-01

## 背景

开通 X 开发者账号时,控制台提示 `Your account has been flagged and cannot proceed`。
在账号被解除标记之前,无法创建 App,也就拿不到 OAuth 2.0 的 Client ID。

## 决策

1. **唯一支持的登录方式是官方 OAuth 2.0 + PKCE。** 本项目不实现、不接受以下方式:
   账号密码登录、导出/导入 cookie(`auth_token`、`ct0`)、浏览器自动化登录、非官方 GraphQL 接口。
2. 原因:
   - X 帮助中心「Automation rules」(搜索摘要,未能读到全文)称:非 API 的自动化(脚本操作网页、
     浏览器自动化、抓取)可能导致账号被永久封禁;登录凭据(密码、token、cookie)不应交给第三方;
     推荐第三方应用使用 OAuth。
   - X 开发者政策(<https://docs.x.com/developer-terms/policy>)原文:
     "You may not ... interfere with, intercept, disrupt, or disable any features of the X API or the X service";
     "Your use case description is binding on you".
   - 账号被标记时改用 cookie/浏览器登录,等于绕过限制,会让账号从"被标记"升级为"被封禁"。
3. 登录之外的"可用性"通过下面的分层策略解决,而不是换一种登录方式。

## 分层策略

| 层 | 条件 | 做法 |
|---|---|---|
| A. 恢复官方 API(主路径) | 账号标记被解除 | 账号健康 → 重新申请/申诉 → `xlogin login` |
| B. 不依赖 X 账号权限的运营流程(过渡) | A 未完成 | 本工具只做内容草稿/排期/审核,发布由人在 x.com 手动完成或用 X 自带定时发布 |
| C. 经 X 审核的第三方 | A 长期不可行 | 通过其官方 OAuth 授权(见 x.com/settings/connected_apps),不向其提供密码 |

## 以后做发帖功能时必须遵守

- 自动化账号需在资料中明确标注,并使用 X 的 Automated account label。
- 采取代表用户的动作(发帖、关注)前须获得明确同意;不得批量关注、跨账号发相同内容。
- 不得超出或规避速率限制;一个用途只注册一个 App。
- 用途说明具有约束力,新增用途要先更新开发者后台的申请。
