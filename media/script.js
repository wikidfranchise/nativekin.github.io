
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('search');
  const articleContainer = document.getElementById('articles');

  fetch('/data/nativekin_aggregated_articles.json')
    .then(response => response.json())
    .then(data => {
      renderArticles(data);

      searchInput.addEventListener('input', () => {
        const term = searchInput.value.toLowerCase();
        const filtered = data.filter(article =>
          article.title.toLowerCase().includes(term) ||
          article.summary.toLowerCase().includes(term) ||
          article.tribe.toLowerCase().includes(term)
        );
        renderArticles(filtered);
      });
    });

  function renderArticles(articles) {
    articleContainer.innerHTML = '';
    articles.forEach(article => {
      const el = document.createElement('article');
      el.classList.add('article');
      el.innerHTML = `
        <h2><a href="${article.link}" target="_blank">${article.title}</a></h2>
        <p class="meta">${article.published || ''} | <strong>${article.tribe}</strong></p>
        <p>${article.summary}</p>
      `;
      articleContainer.appendChild(el);
    });
  }
});
