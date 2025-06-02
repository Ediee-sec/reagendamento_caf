/**
 * Controla a exibição do campo de data específica com base na seleção do filtro
 */
document.addEventListener('DOMContentLoaded', function() {
  const dateFilterSelect = document.getElementById('dateFilterSelect');
  const specificDateGroup = document.getElementById('specificDateGroup');
  
  // Função para atualizar a visibilidade do campo de data específica
  function updateSpecificDateVisibility() {
    const isSpecificDateSelected = dateFilterSelect.value === 'specific';
    
    if (isSpecificDateSelected) {
      specificDateGroup.classList.add('visible');
    } else {
      specificDateGroup.classList.remove('visible');
    }
  }
  
  // Adicionar listener para o select
  dateFilterSelect.addEventListener('change', updateSpecificDateVisibility);
  
  // Verificar estado inicial
  updateSpecificDateVisibility();
});
