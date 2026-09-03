import ApplicationAreaField from "./ApplicationAreaField";
import ChoiceField from "./ChoiceField";
import QuantityUnitField from "./QuantityUnitField";

/** Renders one practice field by its server-declared field_type. Admin
 * configuration selects from a fixed field_type library — it never injects
 * arbitrary markup, so this switch is the complete set of shapes we render. */
export default function DynamicField({ field, value, onChange, locale }) {
  switch (field.field_type) {
    case "APPLICATION_AREA":
      return <ApplicationAreaField field={field} value={value} onChange={onChange} locale={locale} />;

    case "QUANTITY_UNIT":
      return <QuantityUnitField field={field} value={value} onChange={onChange} />;

    case "SINGLE_CHOICE":
    case "PICTURE_CHOICE":
    case "PRODUCT":
    case "PEST":
    case "DISEASE":
      return <ChoiceField field={field} value={value} onChange={onChange} />;

    case "SHORT_TEXT":
      return (
        <input
          type="text"
          value={value || ""}
          onChange={(event) => onChange(event.target.value)}
          maxLength={500}
          className="h-12 w-full rounded-[14px] border-2 border-[#E9E7DC] bg-white px-3 text-base font-medium text-[#1D2117] outline-none focus:border-[#4B6B3A]"
        />
      );

    default:
      return (
        <p className="text-xs text-amber-600">
          This field type ({field.field_type}) isn't supported in this app version yet.
        </p>
      );
  }
}
