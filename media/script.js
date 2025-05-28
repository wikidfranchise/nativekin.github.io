document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('search');
  const articles = document.querySelectorAll('.article');

  searchInput.addEventListener('input', () => {
    const term = searchInput.value.toLowerCase();
    articles.forEach(article => {
      const text = article.innerText.toLowerCase();
      article.style.display = text.includes(term) ? 'block' : 'none';
    });
  });
});
