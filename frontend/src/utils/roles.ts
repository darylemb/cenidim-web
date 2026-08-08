/**
 * Human-readable labels for user roles. The API stores English role
 * keys ("admin" / "editor" / "viewer"); show the Spanish label instead
 * of the raw key so non-technical users understand the tier.
 */
export function roleLabel(role?: string | null): string {
  switch (role) {
    case 'admin':
      return 'Administrador';
    case 'editor':
      return 'Editor';
    case 'viewer':
      return 'Lector';
    default:
      return role ?? '';
  }
}
