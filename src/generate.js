const fs = require("fs");
const Parser = require("rss-parser");
const Handlebars = require("handlebars");

const parser = new Parser({
  headers: {
    "User-Agent": "Mozilla/5.0 (compatible; NativeKinBot/1.0)",
    "Accept": "application/rss+xml, application/xml"
  }
});

const feeds = [
  { name: "Indian Country Today", url: "https://ictnews.org/feed" },
  { name: "Indianz News", url: "https://www.indianz.com/rss/news.xml" },
  { name: "National Native News", url: "https://www.nativenews.net/feed/" },
  { name: "Native America Calling", url: "https://nativeamericacalling.com/feed/" }
];

async function fetchArticles() {
  let articles = [];

  for (const feed of feeds) {
    try {
      const data = await parser.parseURL(feed.url);

      data.items.slice(0, 5).forEach(item => {
        articles.push({
          title: item.title,
          url: item.link || "#",
          source: feed.name
        });
      });

    } catch (err) {
      console.error(`⚠️ Failed to load feed: ${feed.name}`, err.message);
    }
  }

  return articles;
}

async function generatePage() {
  const articles = await fetchArticles();

  const template = `
    <html>
      <head>
        <title>Native Media Feed</title>
        <style>
          body { font-family: sans-serif; padding: 2em; background: #fffaf0; color: #222; }
          h1 { color: #b22222; }
          ul { list-style: none; padding: 0; }
          li { margin-bottom: 1em; }
          .source { font-size: 0.9em; color: #666; }
        </style>
      </head>
      <body>
        <h1>Native Media Feed</h1>
        <ul>
          {{#each articles}}
            <li>
              <a href="{{url}}" target="_blank">{{title}}</a><br>
              <span class="source">Source: {{source}}</span>
            </li>
          {{/each}}
        </ul>
      </body>
    </html>
  `;

  const compiled = Handlebars.compile(template);
  const output = compiled({ articles });

  fs.writeFileSync("media/index.html", html);
  console.log("✅ index.html generated.");
}

generatePage();
