export class ApiError extends Error {
  constructor(message, { status = 0, code = "REQUEST_FAILED", correlationId = null, fields = [], payload = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
    this.fields = fields;
    this.payload = payload;
  }
}
