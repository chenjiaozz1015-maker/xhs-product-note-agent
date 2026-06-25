document.addEventListener('DOMContentLoaded', () => {
  const imageInput = document.getElementById('image-input');
  const preview = document.getElementById('image-preview');
  if (imageInput && preview) {
    const showPlaceholder = () => {
      preview.innerHTML = `
        <div class="upload-placeholder">
          <strong>点击上传商品图片</strong>
          <span>支持 JPG / PNG / WEBP</span>
        </div>
      `;
      preview.classList.remove('has-image');
    };

    const showPreview = (src) => {
      preview.innerHTML = `
        <img src="${src}" alt="上传图片预览" />
        <div class="upload-overlay">点击重新选择</div>
      `;
      preview.classList.add('has-image');
    };

    const openFilePicker = (event) => {
      event?.preventDefault();
      event?.stopPropagation();
      imageInput.click();
    };

    const handleFileSelection = () => {
      const file = imageInput.files && imageInput.files[0];
      if (!file) {
        showPlaceholder();
        return;
      }
      const reader = new FileReader();
      reader.onload = (event) => {
        showPreview(event.target?.result);
      };
      reader.readAsDataURL(file);
    };

    preview.addEventListener('click', openFilePicker);
    preview.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        openFilePicker(event);
      }
    });
    imageInput.addEventListener('click', (event) => {
      event.stopPropagation();
    });
    imageInput.addEventListener('change', handleFileSelection);
    showPlaceholder();
  }

  document.querySelectorAll('.copy-btn').forEach((button) => {
    button.dataset.originalText = button.textContent.trim();
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
        showToast('已复制到剪贴板');
        setTimeout(() => {
          button.textContent = button.dataset.originalText || '一键复制';
        }, 1500);
      } catch (error) {
        button.textContent = '复制失败';
        setTimeout(() => {
          button.textContent = button.dataset.originalText || '一键复制';
        }, 1500);
      }
    });
  });

  const lightbox = document.getElementById('lightbox');
  const lightboxImage = document.getElementById('lightbox-image');
  const lightboxTitle = document.getElementById('lightbox-title');
  const lightboxDownload = document.getElementById('lightbox-download');
  const closeButton = document.querySelector('.lightbox-close');

  const closeLightbox = () => {
    if (!lightbox) return;
    lightbox.hidden = true;
    document.body.style.overflow = '';
  };

  if (lightbox && lightboxImage && closeButton) {
    document.querySelectorAll('.image-card').forEach((card) => {
      card.addEventListener('click', (event) => {
        if (event.target.closest('a')) return;
        const clickedImage = card.querySelector('img');
        if (!clickedImage) return;
        const previewSrc = clickedImage.currentSrc || clickedImage.src;
        if (!previewSrc) return;
        lightboxImage.src = previewSrc;
        lightboxImage.alt = clickedImage.alt || '大图预览';
        if (lightboxTitle) {
          lightboxTitle.textContent = card.dataset.title || '海报预览';
        }
        if (lightboxDownload) {
          lightboxDownload.href = previewSrc;
          lightboxDownload.setAttribute('download', `${card.dataset.name || '种草机图片'}.png`);
        }
        lightbox.hidden = false;
        document.body.style.overflow = 'hidden';
      });
    });

    closeButton.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', (event) => {
      if (event.target === lightbox) {
        closeLightbox();
      }
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        closeLightbox();
      }
    });
  }

  function showToast(message) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 1500);
  }
});
