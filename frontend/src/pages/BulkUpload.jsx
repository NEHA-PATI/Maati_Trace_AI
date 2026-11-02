// Keep the legacy route on the production FPO workflow. The old page was a
// visual demo with fake rows and timed progress, which could imply that data
// had been imported when no backend request had happened.
export { default } from "@/features/fpo/dashboard/FpoImportsPage";
