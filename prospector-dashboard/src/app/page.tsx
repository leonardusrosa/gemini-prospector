import { DashboardShell } from "@/components/DashboardShell";
import { requireOperator } from "@/lib/auth";
import { getCRMRepository } from "@/lib/crm";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const operator = await requireOperator();
  const leads = await getCRMRepository().listLeads();
  const canonical = process.env.CRM_BACKEND === "postgres" && process.env.CRM_MODE === "canonical";
  return <DashboardShell
    initialLeads={leads}
    operatorEmail={operator.email}
    runtime={{
      mode: process.env.CRM_MODE ?? "canonical",
      backend: process.env.CRM_BACKEND ?? "postgres",
      writeEnabled: process.env.CRM_WRITE_ENABLED === "true",
      canonical: canonical ? "SUPABASE_POSTGRES" : "LOCAL_SQLITE",
      remoteStatus: canonical ? "CANONICAL" : "PREVIEW_COPY",
    }}
  />;
}
