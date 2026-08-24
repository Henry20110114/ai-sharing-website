# AI 学习与交流 — 网站源码

一个纯静态网站（HTML + CSS + 少量 JS），无需构建工具，任何静态托管服务都能直接部署。

## 文件结构

```
index.html      首页
courses.html    课程分享（占位）
qa.html         经验答疑（占位）
fields.html     学科方向
news.html       AI 资讯（占位）
about.html      关于
assets/
  style.css     全站样式（配色、排版集中在文件顶部的 :root 变量里）
  main.js       语言切换、移动端菜单
  favicon.svg   站点图标
```

课程、答疑、资讯三个板块目前是占位状态：页面结构和导航都已就绪，等实际内容整理好后，替换页面里的占位提示（`note-panel` 那一块）即可。网站没有放任何联系方式。

## 双语机制

- 默认中文；右上角按钮切换英文，选择保存在浏览器 localStorage（键名 `site-lang`）。
- 页面里所有文字都成对出现：`<span class="zh">中文</span><span class="en">English</span>`。
  修改内容时两个都改；只写一种语言也可以，另一种语言下会不显示。

## 修改内容

- **改文字**：直接编辑对应页面的 HTML。
- **改配色 / 字体**：编辑 `assets/style.css` 顶部的 `:root` 变量。
- **改站名**：搜索替换「AI 学习与交流」和 "AI Learning & Exchange"（出现在每页的页头、页脚和 `<title>` 里）。站标就是纯文字，没有图形 logo；favicon 是 `assets/favicon.svg` 里的 "AI" 两个字母。
- **改样式后浏览器没生效**：把各页面里 `style.css?v=3` 的数字加一（favicon 和 main.js 同理），浏览器就会重新下载。

## 部署到 XiuyuanWang.org（GitHub Pages 方案）

1. 在此文件夹运行：
   ```
   git init && git add -A && git commit -m "Initial site"
   ```
   然后推送到 GitHub 上的一个新仓库。
2. 仓库 Settings → Pages → Source 选 `main` 分支根目录，保存后会得到 `<用户名>.github.io/<仓库名>` 地址。
3. 在 Pages 设置里填入自定义域名 `xiuyuanwang.org`（会自动在仓库里生成 CNAME 文件）。
4. 在 GoDaddy 的 DNS 管理里添加：
   - 4 条 A 记录，主机名 `@`，分别指向：
     `185.199.108.153`、`185.199.109.153`、`185.199.110.153`、`185.199.111.153`
   - 1 条 CNAME 记录，主机名 `www`，指向 `<用户名>.github.io`
5. DNS 生效后（最长 24–48 小时，通常快得多），回到 GitHub Pages 设置勾选 **Enforce HTTPS**。

Netlify / Vercel / Cloudflare Pages 也都可以：直接把整个文件夹拖进去部署，然后按它们的提示在 GoDaddy 配置 DNS 即可。

## 本地预览

双击 `index.html` 即可在浏览器打开；或在此文件夹运行 `python3 -m http.server` 后访问 `http://localhost:8000`。
