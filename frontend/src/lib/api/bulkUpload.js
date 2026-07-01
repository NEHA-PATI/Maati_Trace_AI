import { apiRequest } from "./client";
export const uploadBulkCsv = (file) => {
  const form = new FormData();
  form.append("file", file);
  return apiRequest("/api/bulk-upload", { method: "POST", body: form });
};
export const validateBulkCsv = (file) => uploadBulkCsv(file);
export const processBulkCsv = (file) => uploadBulkCsv(file);
