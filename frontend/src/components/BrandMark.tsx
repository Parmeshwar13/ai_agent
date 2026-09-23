type BrandMarkProps = {
  size?: number;
  tone?: "ink" | "paper";
};

export function BrandMark({ size = 32, tone = "ink" }: BrandMarkProps) {
  const core = tone === "paper" ? "#e7b89a" : "#c4512c";
  const ring = tone === "paper" ? "#d9c7b6" : "#2f6f62";
  const ringTwo = tone === "paper" ? "#f3e6da" : "#c4512c";
  return (
    <svg className="brand-mark" width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <circle cx="16" cy="16" r="3.1" fill={core} />
      <ellipse
        cx="16"
        cy="16"
        rx="12.2"
        ry="5.1"
        fill="none"
        stroke={ring}
        strokeWidth="1.4"
        transform="rotate(-28 16 16)"
      />
      <ellipse
        cx="16"
        cy="16"
        rx="12.2"
        ry="5.1"
        fill="none"
        stroke={ringTwo}
        strokeWidth="1.4"
        opacity={tone === "paper" ? 0.8 : 0.85}
        transform="rotate(34 16 16)"
      />
    </svg>
  );
}
