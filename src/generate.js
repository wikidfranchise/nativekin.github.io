// src/generate.js
const fs = require("fs");
const Parser = require("rss-parser");
const Handlebars = require("handlebars");

const parser = new Parser();
const feeds = [
  { name: "Indian Country Today", url: "https://ictnews.org/feed" },
  // { name: "Indianz News", url: "https://www.indianz.com/rss/news.xml" }, // Disabled due to 406
  { name: "National Native News", url: "https://www.nativenews.net/feed/" },
  { name: "Native America Calling", url: "https://nativeamericacalling.com/feed/" }
];

(async () => {
  const articles = [];

  for (const feedConfig of feeds) {
    try {
      const feed = await parser.parseURL(feedConfig.url);
      feed.items.forEach(item => {
        if (item.title && item.link) {
          articles.push({
            title: item.title,
            url: item.link,
            source: feedConfig.name
          });
        }
      });
    } catch (err) {
      console.warn(`\u26a0\ufe0f Failed to load feed: ${feedConfig.name} ${err.message}`);
    }
  }

  const template = fs.readFileSync("src/template.hbs", "utf8");
  const compile = Handlebars.compile(template);
  const html = compile({ articles });

  fs.mkdirSync("media", { recursive: true });
  fs.writeFileSync("media/index.html", html);

  console.log("\u2705 index.html generated.");
})();
