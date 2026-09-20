# AI无界 · TeenLens AI — 网站源码

纯静态网站（HTML + CSS + 少量 JS），托管在 GitHub Pages，域名 xiuyuanwang.org。
只需要电脑上有 Python 3（Mac 自带），没有其他依赖。

## 文件结构

```
index.html              首页
courses.html            课程分享（占位，内含发布用的示例代码）
qa.html                 经验答疑（占位，内含发布用的示例代码）
fields.html             学科方向
news.html               AI 资讯（占位，内含发布用的示例代码）
about.html              关于
404.html                找不到页面时显示
build.py                构建脚本（见下）
partials/
  head.html             所有页面共用的 <head> 内容：图标、样式、字体、分享预览标签
  header.html           所有页面共用的页头和导航
  footer.html           所有页面共用的页脚
templates/
  article.html          文章页模板：课程讲义、资讯长文都用它
assets/
  style.css             全站样式（配色集中在文件顶部的 :root 变量里）
  main.js               语言切换、移动端菜单
  article.js            文章页专用：自动目录、标题锚点、代码复制按钮
  logo.png              透明背景的站标（页头、页脚）
  favicon-32.png / apple-touch-icon.png   浏览器标签和 iOS 主屏幕图标
  og-image.png          链接分享到聊天软件时显示的预览图
  src/logo-source.jpg   站标原图；上面四张图都由 tools/make_icons.py 从它生成
  images/               文章里用到的图片放这里（需要时自己新建）
.nojekyll               告诉 GitHub Pages 直接发布文件，不做任何处理
CNAME                   自定义域名，不要删
```

联系邮箱 teenlensai@163.com 出现在页脚、关于页和答疑页。

## 构建脚本 build.py

页头、页脚和 `<head>` 里的公共部分只在 `partials/` 里写一份。每个页面用注释标出这三块的位置：

```html
<!-- head -->      ...      <!-- /head -->
<!-- header active="courses" -->   ...   <!-- /header -->
<!-- footer -->    ...      <!-- /footer -->
```

运行 `python3 build.py` 会把 partials 的内容填进每个页面的标记之间，并把所有 `?v=` 版本号统一改成
根据 CSS / JS 内容算出来的哈希值（改了样式访客就会自动重新下载，不用手动改数字）。
`active="..."` 决定导航里哪一项高亮。

**不用记着手动运行**：仓库里装了一个 git pre-commit 钩子（`.git/hooks/pre-commit`），每次 `git commit`
之前会自动运行构建并把改动加进这次提交。如果换了电脑重新 clone，钩子不会跟着走，需要再复制一次：

```sh
printf '#!/bin/sh\ncd "$(git rev-parse --show-toplevel)" || exit 1\npython3 build.py --stage\n' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**改导航 / 页脚 / 图标**：只改 `partials/` 里对应的文件，然后运行 `python3 build.py`（或者直接提交）。

## 发布内容

### 发一篇文章（课程讲义、资讯长文）

```sh
python3 build.py new courses llm-intro-1 大语言模型入门
```

`courses` 是板块（可选 `courses` / `qa` / `fields` / `news`），`llm-intro-1` 是文件名，后面是标题（可省略）。
脚本会生成 `courses/llm-intro-1.html`，填好板块、日期、标题和返回链接，并打印一段可以直接贴到板块页的入口代码。

然后打开生成的文件：
- `<meta name="description">` 写一句简介（分享链接时会显示）
- `post-body zh` 里写中文正文，`post-body en` 里写英文正文
- **没有英文版时**：把 `class="post-body zh"` 改成 `class="post-body"`，删掉整个英文块，中文会在两种语言下都显示
- `post-nav` 是「上一讲 / 下一讲」，改成对应链接；没有的一侧删掉；单篇文章整段删掉

目录（≥ 2 个二级标题时）、标题旁的 # 锚点链接、代码块右上角的复制按钮都由 `article.js` 自动生成，不用手写。
文章页打印或另存为 PDF 时会自动隐藏导航等元素。

模板里的链接都是以 `/` 开头的绝对路径，所以文章放在任何子文件夹里都能正常工作。

### 在板块页加入口

`courses.html`、`qa.html`、`news.html` 里的占位面板下面，各有一段被 `<!-- -->` 注释包住的示例代码：

- 课程：`entry-grid` + `entry-card`，每门课一张卡片
- 资讯：`news-list` + `news-entry`，按日期倒序，短消息可以不带链接直接写
- 问答：`qa-list` + `qa-item`，点击问题展开回答，不需要单独页面

第一次发布时：删掉占位面板，把示例代码从注释里拿出来改成真实内容。之后每次发布只需再加一个条目
（`build.py new` 打印的那段就是）。

## 双语机制

- 首次访问按浏览器语言决定中英文（中文浏览器显示中文，其他显示英文）；右上角按钮切换后会记住选择。
- 短文字成对写：`<span class="zh">中文</span><span class="en">English</span>`。
- 长内容按块写：`<div class="... zh">` 和 `<div class="... en">`。
- 没有 `zh`/`en` 类的元素在两种语言下都显示。

## 字体

页面用「不阻塞渲染」的方式加载 Google Fonts 的思源宋体 / 思源黑体（`partials/head.html` 里 `media="print"` 那一行）。
能访问 Google 的访客会看到 Noto 字体；访问不了的（大陆）页面照常立刻显示，用系统里最接近的字体，不会白屏等待。

## 修改样式

- **改配色**：编辑 `assets/style.css` 顶部的 `:root` 变量。
- **改站名**：搜索替换「AI无界」和 "TeenLens AI"（partials 三个文件、各页面的 `<title>`、首页、模板、`build.py`）。
- **换站标**：把新图放到 `assets/src/logo-source.jpg`（深色图案、浅色背景），然后运行 `python3 tools/make_icons.py`，
  站标、favicon、iOS 图标和分享预览图会自动重新生成（只需要 Mac 自带的 Python 和 sips，约半分钟）。
- **改联系邮箱**：搜索替换 `teenlensai@163.com`（页脚 partial、about.html、qa.html）。

## 本地预览与上线

- 预览：在此文件夹运行 `python3 -m http.server 8000`，浏览器打开 `http://localhost:8000`。
  （页面用的是绝对路径，直接双击 HTML 文件打开会缺样式，要用上面的方式。）
- 上线：`git add -A && git commit -m "说明" && git push`，大约一分钟后 xiuyuanwang.org 就会更新。
  提交时钩子会自动运行构建。

### 域名（已配置好，仅作记录）

GoDaddy DNS：4 条 A 记录 `@` → `185.199.108.153` / `109.153` / `110.153` / `111.153`，
1 条 CNAME `www` → `henry20110114.github.io`。仓库里的 `CNAME` 文件写着 `xiuyuanwang.org`。
