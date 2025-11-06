import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-small font-semibold transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-accent-primary text-text-primary',
        secondary: 'bg-bg-tertiary text-text-secondary border border-border',
        success: 'bg-agent-success text-text-primary',
        warning: 'bg-agent-thinking text-text-primary',
        error: 'bg-agent-error text-text-primary',
        active: 'bg-agent-active text-text-primary',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className = '', variant, ...props }: BadgeProps) {
  return (
    <div className={badgeVariants({ variant, className })} {...props} />
  );
}

export { Badge, badgeVariants };
