export function renderStub(kind) {
  if (kind === "home") {
    return `<section class="page stub-page">
      <div class="stub-hero">
        <h1>End of Season Sale</h1>
        <p>Flat 50–80% off · Wishlist the looks you still want</p>
      </div>
      <div class="cats">
        <div class="cat">Women</div><div class="cat">Men</div>
        <div class="cat">Kids</div><div class="cat">Home</div>
      </div>
      <p class="disclaimer">Home is chrome for this prototype. Open Wishlist or Bag to use the assistant.</p>
    </section>`;
  }
  if (kind === "categories") {
    return `<section class="page stub-page">
      <div class="page-head"><h1 class="page-title">Categories</h1></div>
      <div class="cats">
        <div class="cat">Ethnic wear</div><div class="cat">Footwear</div>
        <div class="cat">Watches</div><div class="cat">Western wear</div>
      </div>
      <p class="disclaimer">Categories is chrome only — shop decisions live on Wishlist.</p>
    </section>`;
  }
  return `<section class="page stub-page">
    <div class="stub-hero">
      <h1>Studio</h1>
      <p>Fashion reels live in the Myntra app. This prototype keeps Wishlist + Bag interactive.</p>
    </div>
  </section>`;
}
