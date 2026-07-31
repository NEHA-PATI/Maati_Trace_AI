export const uploadBulkCsv = async (file) => {
  void file;
  return {
    status: "backend_pending",
    message: "Bulk upload backend pending",
  };
};
export const validateBulkCsv = (file) => uploadBulkCsv(file);
export const processBulkCsv = (file) => uploadBulkCsv(file);
