import { primary, secondary } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

/**
 * Renders a translatable label as a primary line plus a muted secondary line in
 * the other language. English is never hidden: when the farmer picks Odia the
 * English sits underneath, and vice-versa. Pass either a { en, or } `pair` or an
 * explicit `primaryText` / `secondaryText`.
 */
export default function Bilingual({
  pair,
  locale,
  primaryText,
  secondaryText,
  as = "span",
  className,
  secondaryClassName,
}) {
  const Tag = as;
  const main = primaryText ?? primary(pair, locale);
  const sub = secondaryText ?? secondary(pair, locale);
  return (
    <Tag className={cn("block leading-tight", className)}>
      <span className="block">{main}</span>
      {sub ? (
        <span className={cn("block text-[0.72em] font-normal opacity-70", secondaryClassName)}>
          {sub}
        </span>
      ) : null}
    </Tag>
  );
}
