document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.copy-btn').forEach((button) => {
    button.addEventListener('click', async () => {
      const target = button.getAttribute('data-copy-target');
      let text = '';
      const body = document.body.innerText;
      if (target === 'titles') {
        text = Array.from(document.querySelectorAll('li')).map((li) => li.textContent.trim()).join('\n');
      } else if (target === 'body') {
        text = document.querySelector('.card p')?.textContent?.trim() || '';
      } else if (target === 'hashtags') {
        text = document.querySelectorAll('.card p')[1]?.textContent?.trim() || '';
      } else {
        text = body;
      }
      try {
        await navigator.clipboard.writeText(text);
        button.textContent = '已复制';
        setTimeout(() => {
          button.textContent = button.dataset.originalText || '一键复制';
        }, 1200);
      } catch (error) {
        button.textContent = '复制失败';
      }
    });
  });
});
