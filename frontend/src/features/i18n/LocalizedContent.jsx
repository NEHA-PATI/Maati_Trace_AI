import { Children, cloneElement, isValidElement } from "react";

import { translateLiteral } from "./literalTranslations";

const TRANSLATED_ATTRIBUTES = [
  "aria-label",
  "aria-description",
  "placeholder",
  "title",
  "label",
  "description",
  "eyebrow",
];

function localize(value, locale) {
  if (typeof value === "string") return translateLiteral(value, locale);
  if (!isValidElement(value)) return value;

  const props = { ...value.props };
  for (const attribute of TRANSLATED_ATTRIBUTES) {
    if (typeof props[attribute] === "string") props[attribute] = translateLiteral(props[attribute], locale);
  }
  if (props.children !== undefined) {
    props.children = Children.map(props.children, (child) => localize(child, locale));
  }
  return cloneElement(value, props);
}

export function LocalizedContent({ children, locale }) {
  return Children.map(children, (child) => localize(child, locale));
}
