import type { CRMRepository } from "./repository";
import { PostgresCRMRepository } from "./postgres";
import { SQLiteCRMRepository } from "./sqlite";

export function getCRMRepository(): CRMRepository {
  const backend = process.env.CRM_BACKEND ?? "postgres";
  if (backend === "sqlite") {
    const path = process.env.PROSPECTOR_SQLITE_PATH;
    if (!path) throw new Error("Missing PROSPECTOR_SQLITE_PATH");
    return new SQLiteCRMRepository(path, true);
  }
  if (backend === "postgres") return new PostgresCRMRepository();
  throw new Error(`Unsupported CRM_BACKEND: ${backend}`);
}
