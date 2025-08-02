import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-feelori-primary/20 text-feelori-primary",
        secondary:
          "border-transparent bg-white/10 text-white/80",
        destructive:
          "border-transparent bg-red-500/20 text-red-400",
        success:
          "border-transparent bg-green-500/20 text-green-400",
        warning:
          "border-transparent bg-yellow-500/20 text-yellow-400",
        outline: "text-white/70 border-white/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }