interface HeartLogoProps {
  className?: string;
}

export default function HeartLogo({ className = '' }: HeartLogoProps) {
  return (
    <img
      src="/heart.svg"
      alt="LovLov"
      className={className}
    />
  );
}
