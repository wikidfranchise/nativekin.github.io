document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('search');

  // Append fetched articles
  function renderArticles(items) {
    const body = document.querySelector('body');
    items.forEach(item => {
      const article = document.createElement('article');
      article.classList.add('article');
      article.innerHTML = `
        <h2><a href="${item.link}" target="_blank">${item.title}</a></h2>
        <p class="source">${item.pubDate}</p>
        <p>${item.description}</p>
      `;
      body.appendChild(article);
    });
  }

  // Fetch and parse RSS
  fetch('https://rss.nytimes.com/services/xml/rss/nyt/US.xml')  // change to your feed
    .then(response => response.text())
    .then(str => new window.DOMParser().parseFromString(str, "text/xml"))
    .then(data => {
      const items = Array.from(data.querySelectorAll("item")).map(item => ({
        title: item.querySelector("title").textContent,
        link: item.querySelector("link").textContent,
        pubDate: item.querySelector("pubDate").textContent,
        description: item.querySelector("description").textContent
      }));
      renderArticles(items);
    })
    .catch(console.error);

  // Filter
  searchInput.addEventListener('input', () => {
    const term = searchInput.value.toLowerCase();
    const articles = document.querySelectorAll('.article');
    articles.forEach(article => {
      const text = article.innerText.toLowerCase();
      article.style.display = text.includes(term) ? 'block' : 'none';
    });
  });
});
