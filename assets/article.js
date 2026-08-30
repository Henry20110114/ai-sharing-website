// Article pages only: heading anchors, table of contents, copy buttons on code blocks.
(function () {
  function bilingual(zh, en) {
    return '<span class="zh">' + zh + '</span><span class="en">' + en + "</span>";
  }

  document.querySelectorAll(".post-body").forEach(function (body) {
    var headings = body.querySelectorAll("h2, h3");
    var entries = [];
    var used = {};

    headings.forEach(function (h) {
      var text = (h.textContent || "").trim();
      var base = text.replace(/\s+/g, "-").replace(/[#?&/]/g, "") || "section";
      var id = base, n = 2;
      while (used[id] || document.getElementById(id)) { id = base + "-" + n++; }
      used[id] = true;
      h.id = id;
      entries.push({ level: h.tagName, id: id, text: text });

      var anchor = document.createElement("a");
      anchor.className = "anchor";
      anchor.href = "#" + id;
      anchor.textContent = "#";
      anchor.setAttribute("aria-label", "链接到此处 / Link to this section");
      h.appendChild(anchor);
    });

    if (body.querySelectorAll("h2").length >= 2) {
      var toc = document.createElement("nav");
      toc.className = "post-toc";
      toc.setAttribute("aria-label", "目录 / Contents");
      toc.innerHTML = '<span class="post-toc-title">' + bilingual("目录", "Contents") + "</span>";
      var list = document.createElement("ol");
      entries.forEach(function (e) {
        var li = document.createElement("li");
        if (e.level === "H3") li.className = "toc-h3";
        var a = document.createElement("a");
        a.href = "#" + e.id;
        a.textContent = e.text;
        li.appendChild(a);
        list.appendChild(li);
      });
      toc.appendChild(list);
      body.insertBefore(toc, body.firstChild);
    }

    body.querySelectorAll("pre").forEach(function (pre) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "copy-btn";
      btn.innerHTML = bilingual("复制", "Copy");
      btn.addEventListener("click", function () {
        var code = pre.querySelector("code") || pre;
        var text = code.textContent;
        function done() {
          btn.innerHTML = bilingual("已复制", "Copied");
          setTimeout(function () { btn.innerHTML = bilingual("复制", "Copy"); }, 1500);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, done);
        } else {
          var area = document.createElement("textarea");
          area.value = text;
          document.body.appendChild(area);
          area.select();
          try { document.execCommand("copy"); } catch (e) {}
          document.body.removeChild(area);
          done();
        }
      });
      pre.appendChild(btn);
    });
  });
})();
