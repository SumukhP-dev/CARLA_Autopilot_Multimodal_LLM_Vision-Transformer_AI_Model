export default {
  spec_dir: 'src/app/components/simulations',
  spec_files: ['**/*[sS]pec.ts'],
  helpers: ['helpers/**/*.ts'],
  env: {
    stopSpecOnExpectationFailure: false,
    random: true,
  },
};
