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

function somenteNumeros(str) {
        return (str || '').replace(/\D/g, '');
    }

    function mascaraCPF(value) {
        let v = somenteNumeros(value).slice(0, 11);
        if (v.length <= 3) return v;
        if (v.length <= 6) return v.replace(/(\d{3})(\d+)/, '$1.$2');
        if (v.length <= 9) return v.replace(/(\d{3})(\d{3})(\d+)/, '$1.$2.$3');
        return v.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }

    function mascaraTelefone(value) {
        let v = somenteNumeros(value).slice(0, 11);

        if (v.length <= 2) {
            return '(' + v;
        }
        if (v.length <= 6) {
            return v.replace(/(\d{2})(\d+)/, '($1) $2');
        }
        if (v.length <= 10) {
            // Fixo: (11) 1234-5678
            return v.replace(/(\d{2})(\d{4})(\d+)/, '($1) $2-$3');
        }
        // Celular: (11) 91234-5678
        return v.replace(/(\d{2})(\d{5})(\d+)/, '($1) $2-$3');
    }

    document.addEventListener('DOMContentLoaded', function() {
        const cpfInput = document.getElementById('cpf');
        const telInput = document.getElementById('telefone');

        if (cpfInput) {
            // aplica máscara inicial
            cpfInput.value = mascaraCPF(cpfInput.value);

            cpfInput.addEventListener('input', function(e) {
                const cursorPos = this.selectionStart;
                const oldLength = this.value.length;

                this.value = mascaraCPF(this.value);

                const newLength = this.value.length;
                this.selectionStart = this.selectionEnd = cursorPos + (newLength - oldLength);
            });
        }

        if (telInput) {
            telInput.value = mascaraTelefone(telInput.value);

            telInput.addEventListener('input', function(e) {
                const cursorPos = this.selectionStart;
                const oldLength = this.value.length;

                this.value = mascaraTelefone(this.value);

                const newLength = this.value.length;
                this.selectionStart = this.selectionEnd = cursorPos + (newLength - oldLength);
            });
        }
    });