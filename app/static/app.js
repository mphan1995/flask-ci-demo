
async function filterProducts() {
  const q = document.getElementById('q').value.toLowerCase();
  const res = await fetch('/api/products');
  const data = await res.json();
  const grid = document.getElementById('grid');
  const filtered = data.filter(p => (p.name + ' ' + p.brand + ' ' + p.cpu).toLowerCase().includes(q));
  grid.innerHTML = filtered.map(p => `
    <div class="card">
      <img src="${p.img}" alt="${p.name}" loading="lazy">
      <div class="info">
        <h3>${p.name}</h3>
        <p class="meta">${p.brand} • ${p.cpu} • ${p.ram}</p>
        <div class="row">
          <span class="price">$${p.price.toLocaleString()}</span>
          <button class="buy">Thêm vào giỏ</button>
        </div>
      </div>
    </div>
  `).join('');
}
