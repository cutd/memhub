# 发布说明：MemHub Skill

## 建议发布信息

- Slug: `memhub`
- Display name: `MemHub`
- Version: `0.1.3`
- Tags: `memory`, `memhub`, `github`, `gitee`, `sync`, `agent-memory`
- Summary: `跨 Agent 统一记忆仓库 Skill：支持 inbox 写入、canonical 归档、上下文导出，以及 GitHub/Gitee OAuth 同步。`
- Changelog: `将 Skill 名称泛化为 MemHub；完善 Agent 同步行为协议；支持 GitHub/Gitee OAuth、token/SSH fallback；补充同步失败、OAuth 交互、promote 后同步等规则。`

## 包内容

发布包应只包含：

```text
SKILL.md
README.md
scripts/memhub.py
templates/context-pack.md.j2
```

不得包含：

```text
__pycache__/
*.pyc
.git/
.memhub/secrets.yaml
用户个人记忆数据
真实 token / client secret / authorization code
```

## SkillHub.cn 上架流程

1. 打开 `https://skillhub.cn/`。
2. 登录账号。
3. 进入个人中心或点击「发布 Skill」。
4. 如提示实名认证/团队认证，先按平台要求完成。
5. 上传发布包 zip 或文件夹。
6. 填写 Slug、名称、版本、简介、变更说明和标签。
7. 提交并等待安全扫描/审核。

SkillHub Web 端发布接口需要登录态 cookie，当前仓库不保存也不应保存该凭据，因此不能在无登录态环境中代提交。

## ClawHub.ai 上架流程

ClawHub 支持网页上传，也提供 OpenAPI：`https://clawhub.ai/api/v1/openapi.json`。

网页方式：

1. 打开 `https://clawhub.ai/`。
2. 登录账号。
3. 进入发布 Skill 页面。
4. 上传发布包 zip 或文件夹。
5. 填写 Slug、名称、版本、简介、变更说明和标签。
6. 提交。

API 方式需要 Bearer API token。请在安全环境里设置环境变量，不要把 token 写进仓库或聊天记录：

```bash
curl -X POST https://clawhub.ai/api/v1/skills \
  -H "Authorization: Bearer $CLAWHUB_TOKEN" \
  -F 'payload={"slug":"memhub","displayName":"MemHub","version":"0.1.3","changelog":"将 Skill 名称泛化为 MemHub；完善 Agent 同步行为协议；支持 GitHub/Gitee OAuth、token/SSH fallback。","tags":["memory","memhub","github","gitee","sync","agent-memory"]}' \
  -F 'files=@SKILL.md;filename=SKILL.md' \
  -F 'files=@README.md;filename=README.md' \
  -F 'files=@scripts/memhub.py;filename=scripts/memhub.py' \
  -F 'files=@templates/context-pack.md.j2;filename=templates/context-pack.md.j2'
```
