import { primary } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

/**
 * Renders a translatable label in the farmer's ACTIVE language only.
 *
 * V1 UX decision (superseding the earlier "always show English underneath"
 * design): ENGLISH or ODIA, never both on the same screen — mixing the two
 * reads as clutter to a farmer who reads one script. The <LanguageToggle>
 * in every header switches the whole screen, backend included, so nothing
 * is ever lost — it just isn't shown two languages at once. `secondary`
 * from i18n.js still exists for anywhere that deliberately wants the other
 * language (there isn't one in the farmer app), so this component simply
 * ignores it.
 */
export default function Bilingual({
  pair,
  locale,
  primaryText,
  as = "span",
  className,
}) {
  const Tag = as;
  const main = primaryText ?? primary(pair, locale);
  return <Tag className={cn("block leading-tight", className)}>{main}</Tag>;
}
