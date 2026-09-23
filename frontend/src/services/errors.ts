export type FieldErrors = Record<string, string[]>;

export function fieldError(errors: FieldErrors | undefined, name: string) {
  return errors?.[name]?.[0];
}
