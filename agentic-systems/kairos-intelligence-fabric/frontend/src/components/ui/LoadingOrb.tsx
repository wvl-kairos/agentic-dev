import { motion, AnimatePresence } from 'framer-motion'

interface Props {
  isVisible: boolean
}

export function LoadingOrb({ isVisible }: Props) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.0 }}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center"
          style={{ background: '#0a0a1a' }}
        >
          {/* Pulsing orb */}
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.6, 1, 0.6],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            className="w-16 h-16 rounded-full mb-8"
            style={{
              background: 'radial-gradient(circle, #6366f1 0%, #6366f100 70%)',
              boxShadow: '0 0 60px rgba(99, 102, 241, 0.4)',
            }}
          />

          {/* Brand text */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-center"
          >
            <h1
              className="text-2xl font-semibold tracking-wide mb-2"
              style={{ color: '#6366f1' }}
            >
              CEREBRO
            </h1>
            <p
              className="text-sm font-light tracking-widest"
              style={{ color: '#94a3b8' }}
            >
              Connecting the Intelligence Fabric...
            </p>
          </motion.div>

          {/* Subtle progress dots */}
          <div className="flex gap-2 mt-8">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                animate={{ opacity: [0.2, 0.8, 0.2] }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  delay: i * 0.3,
                }}
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: '#6366f1' }}
              />
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
