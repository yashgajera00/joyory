// Helper for loading product photos directly from src/assets
const productImages = import.meta.glob('./*.jpg', { eager: true, import: 'default' });

export function getProductAsset(productId) {
  const key = `./product_${productId}.jpg`;
  return productImages[key] || '';
}

export function getCategoryAsset(categoryName) {
  const key = `./${categoryName}.jpg`;
  return productImages[key] || '';
}

export default productImages;
