import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SortableHeader from '../SortableHeader.vue'

describe('SortableHeader.vue', () => {
  const col = { key: 'name', label: 'Nombre' }

  it('renders the column label', () => {
    const w = mount(SortableHeader, {
      props: { col, sortKey: 'other', sortDir: 'asc' },
    })
    expect(w.find('th').text()).toContain('Nombre')
  })

  it('emits sort with the column key when clicked', async () => {
    const w = mount(SortableHeader, {
      props: { col, sortKey: 'other', sortDir: 'asc' },
    })
    await w.find('th').trigger('click')
    expect(w.emitted('sort')).toEqual([['name']])
  })

  it('shows ▲ when sortDir is asc and this column is the active sort', () => {
    const w = mount(SortableHeader, {
      props: { col, sortKey: 'name', sortDir: 'asc' },
    })
    expect(w.find('.sort-arrow').text()).toBe('▲')
    expect(w.find('.sort-arrow').classes()).toContain('sort-active')
  })

  it('shows ▼ when sortDir is desc and this column is active', () => {
    const w = mount(SortableHeader, {
      props: { col, sortKey: 'name', sortDir: 'desc' },
    })
    expect(w.find('.sort-arrow').text()).toBe('▼')
  })

  it('shows ▲ (placeholder) when this column is not active', () => {
    const w = mount(SortableHeader, {
      props: { col, sortKey: 'other', sortDir: 'asc' },
    })
    expect(w.find('.sort-arrow').text()).toBe('▲')
    expect(w.find('.sort-arrow').classes()).not.toContain('sort-active')
  })
})
