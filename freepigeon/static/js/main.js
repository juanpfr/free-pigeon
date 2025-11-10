import '../css/style.css';
import { createIcons, MapPin, Search, ShoppingCart, ChevronLeft, ChevronRight, LayoutGrid, ArrowLeft, X } from 'lucide';

// Render all icons
createIcons({
  icons: {
    MapPin,
    Search,
    ShoppingCart,
    ChevronLeft,
    ChevronRight,
    LayoutGrid,
    ArrowLeft,
    X
  }
});

// Carousel Logic & Modal Logic
document.addEventListener('DOMContentLoaded', () => {
  // Carousel
  const track = document.querySelector('.carousel-track');
  const prevButton = document.querySelector('.carousel-arrow.prev');
  const nextButton = document.querySelector('.carousel-arrow.next');

  if (track && prevButton && nextButton) {
    const scrollStep = () => {
      const firstItem = track.querySelector('.carousel-item');
      if (!firstItem) return 200;
      const itemStyle = window.getComputedStyle(firstItem);
      const itemWidth = firstItem.offsetWidth;
      const itemMargin = parseFloat(itemStyle.marginRight) || 27;
      return itemWidth + itemMargin;
    };

    nextButton.addEventListener('click', () => {
      track.scrollBy({ left: scrollStep(), behavior: 'smooth' });
    });

    prevButton.addEventListener('click', () => {
      track.scrollBy({ left: -scrollStep(), behavior: 'smooth' });
    });
  }

  // CEP Modal
  const cepModalTriggers = document.querySelectorAll('.cep-modal-trigger');
  const cepModalOverlay = document.getElementById('cep-modal-overlay');
  const cepModalCloseBtn = document.getElementById('cep-modal-close');

  if (cepModalOverlay) {
    cepModalTriggers.forEach(trigger => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        cepModalOverlay.classList.add('visible');
      });
    });

    const closeModal = () => {
      cepModalOverlay.classList.remove('visible');
    }

    if (cepModalCloseBtn) {
      cepModalCloseBtn.addEventListener('click', closeModal);
    }

    cepModalOverlay.addEventListener('click', (e) => {
      if (e.target === cepModalOverlay) {
        closeModal();
      }
    });
  }
});