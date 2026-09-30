import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FilterAlert from '../FilterAlert.vue'

describe('FilterAlert', () => {
  it('offers the commute step with its count', async () => {
    const wrapper = mount(FilterAlert, {
      props: { kind: 'empty', suggestion: { kind: 'step', key: 'commute', value: 20, count: 12 } },
    })
    expect(wrapper.text()).toContain('No listings match your filters.')
    const button = wrapper.get('button')
    expect(button.text()).toBe('Allow up to 20 min → 12 listings')
    await button.trigger('click')
    expect(wrapper.emitted('relax')).toHaveLength(1)
  })

  it('names the filter to drop, including ones it has never seen', () => {
    const wrapper = mount(FilterAlert, {
      props: { kind: 'empty', suggestion: { kind: 'drop', key: 'budget', count: 1 } },
    })
    expect(wrapper.get('button').text()).toBe('Remove Budget filter → 1 listing')
  })

  it('falls back to resetting everything', async () => {
    const wrapper = mount(FilterAlert, { props: { kind: 'empty', suggestion: null } })
    const button = wrapper.get('button')
    expect(button.text()).toBe('Reset all filters')
    await button.trigger('click')
    expect(wrapper.emitted('reset')).toHaveLength(1)
  })

  it('says which filter failed to load, distinct from no results', async () => {
    const wrapper = mount(FilterAlert, { props: { kind: 'error', filterKey: 'beds' } })
    expect(wrapper.text()).toContain("Couldn't load the Beds filter right now.")
    expect(wrapper.text()).not.toContain('No listings match')
    expect(wrapper.classes()).toContain('filter-alert-error')
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('dismiss')).toHaveLength(1)
  })
})
