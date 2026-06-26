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

  const form = document.querySelector('.form-card');
  const formMessage = document.getElementById('form-message');
  if (form && imageInput && formMessage) {
    const submitButton = form.querySelector('button[type="submit"]');
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];

    const showFormMessage = (message, type = 'error') => {
      formMessage.textContent = message;
      formMessage.hidden = false;
      formMessage.className = `form-message form-message-${type}`;
    };

    const restoreSubmit = () => {
      if (!submitButton) return;
      submitButton.disabled = false;
      submitButton.textContent = submitButton.dataset.originalText || '生成种草笔记';
    };

    form.addEventListener('submit', (event) => {
      const file = imageInput.files && imageInput.files[0];
      if (!file) {
        event.preventDefault();
        showFormMessage('请先上传一张商品图片');
        restoreSubmit();
        return;
      }

      if (!allowedTypes.includes(file.type)) {
        event.preventDefault();
        showFormMessage('请上传 JPG、PNG 或 WEBP 格式的商品图片');
        restoreSubmit();
        return;
      }

      const description = form.querySelector('[name="description"]')?.value?.trim() || '';
      if (!description) {
        showFormMessage('可以补充一句商品描述，生成内容会更贴近你的商品', 'warning');
      } else {
        formMessage.hidden = true;
      }

      if (submitButton) {
        submitButton.dataset.originalText = submitButton.textContent.trim();
        submitButton.textContent = '正在生成...';
        submitButton.disabled = true;
      }
    });
  }

  document.querySelectorAll('.copy-btn').forEach((button) => {
    button.dataset.originalText = button.textContent.trim();
    button.addEventListener('click', async () => {
      const target = button.getAttribute('data-copy-target');
      const text = getCopyText(target, button);
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

  document.querySelectorAll('.download-all-btn').forEach((button) => {
    button.addEventListener('click', () => {
      const links = Array.from(document.querySelectorAll('.single-download'));
      links.forEach((link, index) => {
        window.setTimeout(() => {
          const download = document.createElement('a');
          download.href = link.href;
          download.download = link.getAttribute('download') || `小红书素材图${index + 1}.png`;
          document.body.appendChild(download);
          download.click();
          download.remove();
        }, index * 250);
      });
      showToast('已开始下载，如浏览器拦截请分别点击单张下载');
    });
  });

  const noteBodyDisplay = document.getElementById('note-body-display');
  const noteBodyEditor = document.getElementById('note-body-editor');
  const editNoteBodyButton = document.getElementById('edit-note-body-button');

  if (noteBodyDisplay && noteBodyEditor && editNoteBodyButton) {
    editNoteBodyButton.addEventListener('click', () => {
      const isEditing = !noteBodyEditor.hidden;
      if (isEditing) {
        const updatedBody = noteBodyEditor.value.trim();
        noteBodyDisplay.textContent = updatedBody;
        noteBodyDisplay.dataset.currentNoteBody = updatedBody;
        noteBodyDisplay.hidden = false;
        noteBodyEditor.hidden = true;
        editNoteBodyButton.textContent = '编辑正文';
        editNoteBodyButton.classList.remove('btn-primary');
        editNoteBodyButton.classList.add('btn-ghost');
        showToast('正文已更新');
        return;
      }

      noteBodyEditor.value = noteBodyDisplay.dataset.currentNoteBody || noteBodyDisplay.textContent.trim();
      noteBodyDisplay.hidden = true;
      noteBodyEditor.hidden = false;
      noteBodyEditor.focus();
      editNoteBodyButton.textContent = '保存修改';
      editNoteBodyButton.classList.remove('btn-ghost');
      editNoteBodyButton.classList.add('btn-primary');
    });
  }

  setupEditableList({
    displayId: 'titles-display',
    editorId: 'titles-editor',
    hintId: 'titles-editor-hint',
    buttonId: 'edit-titles-button',
    itemSelector: 'li',
    maxItems: 5,
    editText: '编辑标题',
    saveText: '保存标题',
    savedText: '标题已更新',
    renderItem: (text) => {
      const item = document.createElement('li');
      item.textContent = text;
      return item;
    },
  });

  setupEditableList({
    displayId: 'tags-display',
    editorId: 'tags-editor',
    hintId: 'tags-editor-hint',
    buttonId: 'edit-tags-button',
    itemSelector: 'span',
    maxItems: 12,
    editText: '编辑标签',
    saveText: '保存标签',
    savedText: '标签已更新',
    normalize: normalizeTags,
    joinText: (items) => items.join(' '),
    renderItem: (text) => {
      const item = document.createElement('span');
      item.textContent = text;
      return item;
    },
  });

  setupEditableList({
    displayId: 'comments-display',
    editorId: 'comments-editor',
    hintId: 'comments-editor-hint',
    buttonId: 'edit-comments-button',
    itemSelector: 'p',
    maxItems: 5,
    editText: '编辑评论引导',
    saveText: '保存评论引导',
    savedText: '评论引导已更新',
    renderItem: (text) => {
      const item = document.createElement('p');
      item.textContent = text;
      return item;
    },
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
    const openLightbox = (event, clickedImage) => {
      const card = clickedImage.closest('.image-card');
      if (!card) return;

      event.preventDefault();
      event.stopPropagation();

      const previewSrc = clickedImage.src;
      if (!previewSrc) return;

      lightboxImage.src = previewSrc;
      lightboxImage.alt = clickedImage.alt || '大图预览';
      lightboxImage.style.display = 'block';

      if (lightboxTitle) {
        lightboxTitle.textContent = card.dataset.title || '海报预览';
      }
      if (lightboxDownload) {
        lightboxDownload.href = previewSrc;
        lightboxDownload.setAttribute('download', `${card.dataset.name || '种草机图片'}.png`);
      }

      lightbox.hidden = false;
      document.body.style.overflow = 'hidden';
    };

    document.querySelectorAll('.image-card img').forEach((image) => {
      image.addEventListener('click', (event) => {
        openLightbox(event, image);
      });
    });

    document.querySelectorAll('.image-card a').forEach((link) => {
      const image = link.querySelector('img');
      if (!image) return;

      link.addEventListener('click', (event) => {
        openLightbox(event, image);
      });
    });

    document.querySelectorAll('.image-actions a').forEach((downloadLink) => {
      downloadLink.addEventListener('click', (event) => {
        event.stopPropagation();
      });
    });

    closeButton.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      closeLightbox();
    });

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

  function getCopyText(target, sourceButton) {
    if (target === 'titles') {
      const editor = document.getElementById('titles-editor');
      const titles = editor && !editor.hidden
        ? normalizeLines(editor.value, 5)
        : getDisplayItems('titles-display', 'li');

      return titles
        .map((item, index) => `${index + 1}. ${item}`)
        .filter(Boolean)
        .join('\n');
    }
    if (target === 'body') {
      const editor = document.getElementById('note-body-editor');
      if (editor && !editor.hidden) {
        return editor.value.trim();
      }
      const display = document.querySelector('[data-copy-source="body"]');
      return display?.dataset?.currentNoteBody || display?.textContent?.trim() || '';
    }
    if (target === 'hashtags') {
      const editor = document.getElementById('tags-editor');
      if (editor && !editor.hidden) {
        return normalizeTags(editor.value).join(' ');
      }

      return getDisplayItems('tags-display', 'span')
        .join(' ');
    }
    if (target === 'comments') {
      const editor = document.getElementById('comments-editor');
      if (editor && !editor.hidden) {
        return normalizeLines(editor.value, 5).join('\n');
      }

      return getDisplayItems('comments-display', 'p')
        .join('\n');
    }
    if (target === 'trial-feedback') {
      return [
        '【种草机试用反馈】',
        '1. 我测试的商品类型：',
        '2. 生成图片效果：满意 / 一般 / 不满意',
        '3. 文案是否贴合商品：贴合 / 一般 / 不贴合',
        '4. 哪一步不好用：',
        '5. 我最希望增加的功能：',
        '6. 其他建议：',
      ].join('\n');
    }
    if (target === 'result-feedback') {
      const productName = sourceButton?.dataset?.productName || '';
      const category = sourceButton?.dataset?.category || '';
      return [
        '【种草机生成结果反馈】',
        `1. 商品名称：${productName}`,
        `2. 商品类目：${category}`,
        '3. 图片效果是否像小红书：像 / 一般 / 不像',
        '4. 文案是否贴合商品：贴合 / 一般 / 不贴合',
        '5. 哪张图最有用：封面图 / 卖点图 / 总结图',
        '6. 哪个结果不满意：',
        '7. 希望增加的功能：',
      ].join('\n');
    }

    const titles = getCopyText('titles');
    const body = getCopyText('body');
    const hashtags = getCopyText('hashtags');
    const comments = getCopyText('comments');
    return [
      buildCopySection('标题候选', titles),
      buildCopySection('正文', body, true),
      buildCopySection('标签', hashtags),
      buildCopySection('评论引导', comments),
    ]
      .filter(Boolean)
      .join('\n\n');
  }

  function setupEditableList(options) {
    const display = document.getElementById(options.displayId);
    const editor = document.getElementById(options.editorId);
    const hint = document.getElementById(options.hintId);
    const button = document.getElementById(options.buttonId);
    if (!display || !editor || !button) return;

    const normalize = options.normalize || ((value) => normalizeLines(value, options.maxItems));
    const joinText = options.joinText || ((items) => items.join('\n'));

    button.addEventListener('click', () => {
      const isEditing = !editor.hidden;
      const currentItems = getDisplayItems(options.displayId, options.itemSelector);

      if (isEditing) {
        const nextItems = normalize(editor.value);
        const itemsToSave = nextItems.length ? nextItems : currentItems;
        renderEditableItems(display, itemsToSave, options.renderItem);
        editor.value = joinText(itemsToSave);
        display.hidden = false;
        editor.hidden = true;
        if (hint) hint.hidden = true;
        setEditButtonState(button, false, options.editText);
        showToast(options.savedText);
        return;
      }

      editor.value = joinText(currentItems);
      display.hidden = true;
      editor.hidden = false;
      if (hint) hint.hidden = false;
      setEditButtonState(button, true, options.saveText);
      editor.focus();
    });
  }

  function setEditButtonState(button, isEditing, text) {
    button.textContent = text;
    button.classList.toggle('btn-primary', isEditing);
    button.classList.toggle('btn-ghost', !isEditing);
  }

  function getDisplayItems(displayId, selector) {
    const display = document.getElementById(displayId);
    if (!display) return [];

    return Array.from(display.querySelectorAll(selector))
      .map((item) => item.textContent.trim())
      .filter(Boolean);
  }

  function renderEditableItems(display, items, renderItem) {
    display.textContent = '';
    items.forEach((text) => {
      display.appendChild(renderItem(text));
    });
  }

  function normalizeLines(value, limit) {
    return value
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .slice(0, limit);
  }

  function normalizeTags(value) {
    const seen = new Set();
    return value
      .split(/[\s,，]+/)
      .map((tag) => tag.trim())
      .filter(Boolean)
      .map((tag) => (tag.startsWith('#') ? tag : `#${tag}`))
      .filter((tag) => {
        if (seen.has(tag)) return false;
        seen.add(tag);
        return true;
      })
      .slice(0, 12);
  }

  function buildCopySection(label, content, keepWhenEmpty = false) {
    const text = (content || '').trim();
    if (!text && !keepWhenEmpty) return '';
    return `${label}：\n${text}`;
  }
});
