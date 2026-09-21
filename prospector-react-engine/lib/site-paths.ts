export const SITE_BASE_PATH = "/clientes/dallas-detailing-and-buffing";

export function assetPath(asset: string): string {
  return `${SITE_BASE_PATH}/assets/${asset.replace(/^\/+/, "")}`;
}
